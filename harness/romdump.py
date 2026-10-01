"""
Minimal from-scratch DUSB + custom-ROM-dump-protocol client for the TI-84 Plus
(non-CE, non-SE) over its USB DirectLink, implemented directly against the
protocol as documented in the open-source tilibs project (debrouxl/tilibs),
specifically libticalcs/trunk/src/{dusb_rpkt,dusb_vpkt,dusb_cmd,calc_84p,romdump}.cc

This exists because the Ubuntu-packaged tilp/libticables build fails every
ROM-dump attempt with ERR_INVALID_PACKET ("Invalid packet: a transmission
error") at 0% progress, regardless of USB port, cable topology, timeout
settings, or a full calculator power-cycle -- five consecutive identical
failures ruled out a hardware/link explanation. Reimplementing the protocol
directly gives full visibility into every byte exchanged instead of an
opaque GUI error, and bypasses whatever bug is in that packaged build.

Usage: run as a script. Requires pyusb (`pip install pyusb`) and the ROM
dumper program already sent to the calculator as a program named ROMDUMP
(see ROMDUMP_84p.8xp, extracted byte-for-byte from tilibs' rom84p.h).
"""
import sys
import time
import usb.core
import usb.util

VID, PID = 0x0451, 0xE003
EP_OUT, EP_IN = 0x02, 0x81
TIMEOUT_MS = 8000

# --- DUSB raw packet types ---
RPKT_BUF_SIZE_REQ = 1
RPKT_BUF_SIZE_ALLOC = 2
RPKT_VIRT_DATA = 3
RPKT_VIRT_DATA_LAST = 4
RPKT_VIRT_DATA_ACK = 5

# --- DUSB virtual packet types ---
VPKT_PING = 0x0001
VPKT_PARM_REQ = 0x0007
VPKT_PARM_DATA = 0x0008
VPKT_EXECUTE = 0x0011
VPKT_MODE_SET = 0x0012
VPKT_DATA_ACK = 0xAA00
VPKT_DELAY_ACK = 0xBB00
VPKT_EOT = 0xDD00
VPKT_ERROR = 0xEE00

DUSB_DH_SIZE = 6  # 4-byte size + 2-byte type, prefixed to the FIRST raw fragment only
DUSB_EID_PRGM = 0x00

# --- romdump.cc custom raw protocol (used only after ROMDUMP program is launched) ---
CMD_IS_READY = 0xAA55
CMD_KO = 0x0000
CMD_OK = 0x0001
CMD_EXIT = 0x0002
CMD_REQ_SIZE = 0x0003
CMD_REQ_BLOCK = 0x0005
CMD_DATA1 = 0x0006
CMD_DATA2 = 0x0007


VERBOSE = __name__ == "__main__"


def log(msg):
    if VERBOSE:
        print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def checksum(data):
    return sum(data) & 0xFFFF


class ProtocolError(Exception):
    pass


class Link:
    def __init__(self):
        self.dev = usb.core.find(idVendor=VID, idProduct=PID)
        if self.dev is None:
            raise RuntimeError("Calculator not found on USB")
        try:
            if self.dev.is_kernel_driver_active(0):
                self.dev.detach_kernel_driver(0)
        except (NotImplementedError, usb.core.USBError):
            pass
        self.dev.set_configuration()
        usb.util.claim_interface(self.dev, 0)
        self.rpkt_maxlen = 250  # default until negotiated
        self._rx_buf = bytearray()

    def close(self):
        try:
            usb.util.release_interface(self.dev, 0)
        except Exception:
            pass

    # --- raw cable I/O, mirroring ticables_cable_send/recv ---
    def cable_send(self, data):
        n = self.dev.write(EP_OUT, data, timeout=TIMEOUT_MS)
        if n != len(data):
            raise ProtocolError(f"short write: sent {n}, expected {len(data)}")

    def _fill_rx(self, min_bytes):
        # The device packs replies into single USB transactions that may be
        # larger than any one logical field we want to parse (e.g. the whole
        # 9-byte BUF_SIZE_ALLOC reply arrives as one transfer). Requesting an
        # exact small length via pyusb's read() throws EOVERFLOW when the
        # device actually sent more than that in one transaction, since
        # libusb cannot safely truncate. So we always read into a generous
        # fixed-size buffer and keep any surplus queued for the next call.
        while len(self._rx_buf) < min_bytes:
            chunk = self.dev.read(EP_IN, 4096, timeout=TIMEOUT_MS)
            self._rx_buf.extend(chunk)
            if len(chunk) == 0:
                # genuine zero-length packet from the device; don't spin
                break

    def cable_recv(self, length):
        if length == 0:
            # explicit ZLP-consuming read (workaround_send/recv): only
            # actually hit the wire if we have nothing buffered, since a
            # buffered surplus means there's nothing left on the wire to
            # consume right now.
            if not self._rx_buf:
                try:
                    self.dev.read(EP_IN, 1, timeout=200)
                except usb.core.USBError:
                    pass
            return b""
        self._fill_rx(length)
        if len(self._rx_buf) < length:
            raise ProtocolError(f"short read: got {len(self._rx_buf)}, expected {length}")
        out = bytes(self._rx_buf[:length])
        del self._rx_buf[:length]
        return out

    # --- DUSB raw packet layer ---
    def dusb_send_raw(self, rtype, data):
        size = len(data)
        buf = bytes([
            (size >> 24) & 0xFF, (size >> 16) & 0xFF,
            (size >> 8) & 0xFF, size & 0xFF,
            rtype,
        ]) + data
        self.cable_send(buf)

    def dusb_recv_raw(self):
        hdr = self.cable_recv(5)
        size = int.from_bytes(hdr[0:4], "big")
        rtype = hdr[4]
        if size > 2048:
            raise ProtocolError(f"raw packet size implausible: {size}")
        data = self.cable_recv(size) if size else b""
        return rtype, data

    # --- ZLP workarounds, ported from dusb_vpkt.cc for CALC_TI84P_USB ---
    def workaround_send(self, raw_type, raw_size, vtl_size):
        if raw_type == RPKT_VIRT_DATA_LAST and vtl_size > 244 and (vtl_size % 250) == 244:
            log(f"  [workaround_send] extra ZLP write (vtl_size={vtl_size})")
            self.cable_send(b"")

    def workaround_recv(self, raw_size):
        if ((raw_size + 5) % 64) == 0:
            log(f"  [workaround_recv] extra ZLP read (raw_size={raw_size})")
            self.cable_recv(0)

    # --- DUSB virtual packet layer ---
    def dusb_send_data(self, vtype, data):
        vsize = len(data)
        maxlen = self.rpkt_maxlen
        if vsize <= maxlen - DUSB_DH_SIZE:
            payload = vsize.to_bytes(4, "big") + vtype.to_bytes(2, "big") + data
            self.dusb_send_raw(RPKT_VIRT_DATA_LAST, payload)
            log(f"  PC->TI: raw VIRT_DATA_LAST (vtl_size={vsize}, vtype=0x{vtype:04x})")
            self.workaround_send(RPKT_VIRT_DATA_LAST, len(payload), vsize)
            self.dusb_recv_acknowledge()
        else:
            first_len = maxlen - DUSB_DH_SIZE
            payload = vsize.to_bytes(4, "big") + vtype.to_bytes(2, "big") + data[:first_len]
            self.dusb_send_raw(RPKT_VIRT_DATA, payload)
            log(f"  PC->TI: raw VIRT_DATA (first fragment, vtl_size={vsize})")
            self.dusb_recv_acknowledge()

            offset = first_len
            remaining = vsize - offset
            q, r = divmod(remaining, maxlen)
            for _ in range(q):
                chunk = data[offset:offset + maxlen]
                self.dusb_send_raw(RPKT_VIRT_DATA, chunk)
                log(f"  PC->TI: raw VIRT_DATA (continuation, {len(chunk)}B)")
                self.dusb_recv_acknowledge()
                offset += maxlen
            chunk = data[offset:offset + r]
            self.dusb_send_raw(RPKT_VIRT_DATA_LAST, chunk)
            log(f"  PC->TI: raw VIRT_DATA_LAST (final, {len(chunk)}B)")
            # per source: workaround_send skipped here for TI84P_USB
            self.dusb_recv_acknowledge()

    def dusb_recv_data(self):
        vtl_type = None
        vtl_data = b""
        declared_size = None
        first = True
        while True:
            rtype, rdata = self.dusb_recv_raw()
            if rtype not in (RPKT_VIRT_DATA, RPKT_VIRT_DATA_LAST):
                raise ProtocolError(f"Unexpected raw packet type: {rtype} (expected VIRT_DATA/VIRT_DATA_LAST)")
            if first:
                first = False
                if len(rdata) < DUSB_DH_SIZE:
                    raise ProtocolError("First raw packet too small")
                declared_size = int.from_bytes(rdata[0:4], "big")
                vtl_type = int.from_bytes(rdata[4:6], "big")
                vtl_data = rdata[DUSB_DH_SIZE:]
                log(f"  TI->PC: raw {'VIRT_DATA_LAST' if rtype == RPKT_VIRT_DATA_LAST else 'VIRT_DATA'}"
                    f" (declared_size={declared_size}, vtype=0x{vtl_type:04x})")
            else:
                vtl_data += rdata
                log(f"  TI->PC: raw {'VIRT_DATA_LAST' if rtype == RPKT_VIRT_DATA_LAST else 'VIRT_DATA'}"
                    f" (+{len(rdata)}B, total={len(vtl_data)})")

            self.workaround_recv(len(rdata))
            self.dusb_send_acknowledge()

            if rtype == RPKT_VIRT_DATA_LAST:
                break

        if declared_size != len(vtl_data):
            raise ProtocolError(f"declared size {declared_size} != actual {len(vtl_data)}")
        return vtl_type, vtl_data

    def dusb_send_acknowledge(self):
        self.dusb_send_raw(RPKT_VIRT_DATA_ACK, bytes([0xE0, 0x00]))

    def dusb_recv_acknowledge(self):
        rtype, rdata = self.dusb_recv_raw()
        if rtype == RPKT_BUF_SIZE_REQ:
            if len(rdata) != 4:
                raise ProtocolError("bad BUF_SIZE_REQ during ack wait")
            size = int.from_bytes(rdata, "big")
            log(f"  TI->PC: Buffer Size Request ({size} bytes) [mid-ack]")
            self.dusb_send_buf_size_alloc(size)
            rtype, rdata = self.dusb_recv_raw()
        if rtype != RPKT_VIRT_DATA_ACK:
            raise ProtocolError(f"expected VIRT_DATA_ACK, got raw type {rtype}")
        if rdata[0:2] != bytes([0xE0, 0x00]):
            log(f"  [warn] ack payload unexpected: {rdata.hex()}")

    def dusb_send_buf_size_request(self, size):
        self.dusb_send_raw(RPKT_BUF_SIZE_REQ, size.to_bytes(4, "big"))
        log(f"  PC->TI: Buffer Size Request ({size} bytes)")

    def dusb_recv_buf_size_alloc(self):
        rtype, rdata = self.dusb_recv_raw()
        if rtype != RPKT_BUF_SIZE_ALLOC or len(rdata) != 4:
            raise ProtocolError("expected BUF_SIZE_ALLOC")
        size = int.from_bytes(rdata, "big")
        size = min(size, 2048)
        self.rpkt_maxlen = size
        log(f"  TI->PC: Buffer Size Allocation ({size} bytes)")
        return size

    def dusb_send_buf_size_alloc(self, size):
        self.dusb_send_raw(RPKT_BUF_SIZE_ALLOC, size.to_bytes(4, "big"))
        self.rpkt_maxlen = size

    # --- command layer ---
    def mode_set_ping(self):
        self.dusb_send_buf_size_request(1024)
        self.dusb_recv_buf_size_alloc()
        mode = (3, 1, 0, 0, 0x07D0)
        payload = b"".join(v.to_bytes(2, "big") for v in mode)
        log(f"  PC->TI: Ping/Set Mode {mode}")
        self.dusb_send_data(VPKT_PING, payload)
        vtype, vdata = self.dusb_recv_data()
        if vtype == VPKT_ERROR:
            raise ProtocolError(f"calc returned error during mode set: {vdata.hex()}")
        if vtype != VPKT_MODE_SET:
            raise ProtocolError(f"expected MODE_SET ack, got 0x{vtype:04x}")
        log("  TI->PC: Acknowledgement of Mode Setting")

    def execute(self, folder, name, action, args=b"", code=0):
        payload = bytes([len(folder)])
        if name:
            payload += bytes([len(name)]) + name.encode() + b"\x00"
        else:
            payload += bytes([0])
        payload += bytes([action])
        payload += args
        log(f"  PC->TI: Execute action={action} name={name!r}")
        self.dusb_send_data(VPKT_EXECUTE, payload)

    def recv_data_ack(self):
        vtype, vdata = self.dusb_recv_data()
        if vtype == VPKT_ERROR:
            raise ProtocolError(f"calc returned error: {vdata.hex()}")
        if vtype != VPKT_DATA_ACK:
            raise ProtocolError(f"expected DATA_ACK, got 0x{vtype:04x}")
        log("  TI->PC: Acknowledgement of Data")

    # --- romdump.cc custom raw protocol (post-launch, bypasses DUSB vpkt layer) ---
    def rd_send_pkt(self, cmd, data=b""):
        buf = cmd.to_bytes(2, "little") + len(data).to_bytes(2, "little") + data
        buf += checksum(buf).to_bytes(2, "little")
        self.cable_send(buf)

    def rd_recv_pkt(self):
        hdr = self.cable_recv(4)
        cmd = int.from_bytes(hdr[0:2], "little")
        length = int.from_bytes(hdr[2:4], "little")
        if length:
            body = self.cable_recv(length)
        else:
            body = b""
        chk = self.cable_recv(2)
        full = hdr + body
        expect = checksum(full) & 0xFFFF
        got = int.from_bytes(chk, "little")
        if expect != got:
            raise ProtocolError(f"romdump checksum mismatch: expected {expect:04x}, got {got:04x}")
        return cmd, body

    def rd_is_ready(self):
        self.rd_send_pkt(CMD_IS_READY)
        cmd, body = self.rd_recv_pkt()
        log(f"  TI->PC: {'OK' if cmd else 'KO'} (cmd=0x{cmd:04x})")
        return cmd

    def rd_req_size(self):
        self.rd_send_pkt(CMD_REQ_SIZE)
        cmd, body = self.rd_recv_pkt()
        size = int.from_bytes(body[0:4], "little")
        log(f"  TI->PC: SIZE = 0x{size:08x} ({size} bytes)")
        return size

    def rd_req_block(self, addr):
        self.rd_send_pkt(CMD_REQ_BLOCK, addr.to_bytes(4, "little"))
        cmd, body = self.rd_recv_pkt()
        if cmd == CMD_DATA1:
            return body
        elif cmd == CMD_DATA2:
            size = int.from_bytes(body[0:2], "little")
            rpt = body[2]
            return bytes([rpt]) * size
        else:
            raise ProtocolError(f"unexpected romdump cmd 0x{cmd:04x}")

    def rd_exit(self):
        self.rd_send_pkt(CMD_EXIT)
        self.rd_recv_pkt()


def dump_rom(out_path):
    link = Link()
    try:
        log("=== Mode set (ping) ===")
        link.mode_set_ping()

        log("=== Launching ROMDUMP program ===")
        link.execute("", "ROMDUMP", DUSB_EID_PRGM)
        link.recv_data_ack()

        log("Waiting 3s for dumper to start...")
        time.sleep(3)

        log("=== Custom ROM dump protocol ===")
        for attempt in range(3):
            log(f"-- RDY handshake attempt {attempt + 1} --")
            cmd = link.rd_is_ready()
            if cmd:
                break
        else:
            raise ProtocolError("calc never became ready")

        size = link.rd_req_size()
        log(f"ROM size: {size} bytes")

        with open(out_path, "wb") as f:
            addr = 0
            t0 = time.time()
            while addr < size:
                block = link.rd_req_block(addr)
                f.write(block)
                addr += len(block)
                if addr % 8192 < len(block):
                    elapsed = time.time() - t0
                    rate = addr / elapsed / 1024 if elapsed > 0 else 0
                    log(f"  progress: {addr}/{size} bytes ({100 * addr / size:.1f}%, {rate:.1f} KB/s)")

        log("=== Sending EXIT ===")
        link.rd_exit()
        log(f"DONE. ROM saved to {out_path} ({addr} bytes)")
    finally:
        link.close()


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "ti84p_dump.rom"
    dump_rom(out)
