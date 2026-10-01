/* Headless TI-84 Plus harness around libtilemcore (TilEm 2.0).
   Exposes a tiny C API for Python ctypes: run, keys, graylink bytes, LCD. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include "tilem.h"

/* --- helpers the core expects the frontend to provide --- */
void *tilem_malloc(size_t s) { void *p = malloc(s); if (!p) abort(); return p; }
void *tilem_malloc0(size_t s) { void *p = calloc(1, s); if (!p) abort(); return p; }
void *tilem_malloc_atomic(size_t s) { return tilem_malloc(s); }
void *tilem_try_malloc(size_t s) { return malloc(s); }
void *tilem_try_malloc0(size_t s) { return calloc(1, s); }
void *tilem_try_malloc_atomic(size_t s) { return malloc(s); }
void *tilem_realloc(void *p, size_t s) { void *q = realloc(p, s); if (s && !q) abort(); return q; }
void tilem_free(void *p) { free(p); }
static int verbose = 0;
static void vlog(const char *k, const char *m, va_list a)
{ if (!verbose) return; fprintf(stderr, "[tilem %s] ", k); vfprintf(stderr, m, a); fputc('\n', stderr); }
void tilem_message(TilemCalc *c, const char *m, ...) { va_list a; va_start(a, m); vlog("msg", m, a); va_end(a); }
void tilem_warning(TilemCalc *c, const char *m, ...) { va_list a; va_start(a, m); vlog("warn", m, a); va_end(a); }
void tilem_internal(TilemCalc *c, const char *m, ...) { va_list a; va_start(a, m); vlog("INTERNAL", m, a); va_end(a); }

#define LINK_EVENTS (TILEM_STOP_LINK_READ_BYTE | TILEM_STOP_LINK_WRITE_BYTE | TILEM_STOP_LINK_ERROR)
#define TICK 10000

void th_set_verbose(int v) { verbose = v; }

TilemCalc *th_open(const char *rom, const char *sav)
{
	FILE *rf = fopen(rom, "rb"), *sf = NULL;
	TilemCalc *c;
	if (!rf) return NULL;
	if (sav && *sav) sf = fopen(sav, "rb");
	c = tilem_calc_new(TILEM_CALC_TI84P);
	if (!c) { fclose(rf); return NULL; }
	if (tilem_calc_load_state(c, rf, sf)) { tilem_calc_free(c); c = NULL; }
	fclose(rf);
	if (sf) fclose(sf);
	return c;
}

int th_save(TilemCalc *c, const char *rom, const char *sav)
{
	FILE *rf = fopen(rom, "wb"), *sf = fopen(sav, "wb");
	int r;
	if (!rf || !sf) return -1;
	r = tilem_calc_save_state(c, rf, sf);
	fclose(rf); fclose(sf);
	return r;
}

void th_close(TilemCalc *c) { tilem_calc_free(c); }
void th_reset(TilemCalc *c) { tilem_calc_reset(c); }

/* Run for `us` microseconds of emulated time. Returns OR of stop reasons. */
unsigned th_run(TilemCalc *c, int us)
{
	unsigned ev = 0; int rem;
	c->linkport.linkemu = TILEM_LINK_EMULATOR_GRAY;
	c->z80.stop_mask = ~(dword)0;   /* never stop early */
	while (us > 0) {
		int t = us < TICK ? us : TICK;
		ev |= tilem_z80_run_time(c, t, &rem);
		us -= t;
	}
	return ev;
}

void th_key_down(TilemCalc *c, int k) { tilem_keypad_press_key(c, k); }
void th_key_up(TilemCalc *c, int k) { tilem_keypad_release_key(c, k); }

int th_asleep(TilemCalc *c)
{ return c->z80.halted && !c->z80.interrupts && !c->poweronhalt; }

static int run_link(TilemCalc *c, int us, int (*done)(TilemCalc *, int *), int *out)
{
	int rem;
	c->linkport.linkemu = TILEM_LINK_EMULATOR_GRAY;
	c->z80.stop_mask = ~(dword)(LINK_EVENTS);
	while (us > 0) {
		dword ev;
		int t = us < TICK ? us : TICK;
		if (done(c, out)) return 0;
		ev = tilem_z80_run_time(c, t, &rem);
		us -= (t - rem);
		if (ev & TILEM_STOP_LINK_ERROR) return -2;
	}
	return done(c, out) ? 0 : -1;
}
static int is_ready(TilemCalc *c, int *o) { (void)o; return tilem_linkport_graylink_ready(c); }
static int got_byte(TilemCalc *c, int *o) { int v = tilem_linkport_graylink_get_byte(c); if (v >= 0) { *o = v; return 1; } return 0; }

/* Send one byte over the virtual graylink. 0 = ok, <0 = timeout/error. */
int th_send_byte(TilemCalc *c, int b, int timeout_us)
{
	int r;
	if ((r = run_link(c, timeout_us, is_ready, NULL))) return r;
	if (tilem_linkport_graylink_send_byte(c, (byte)b)) return -3;
	return run_link(c, timeout_us, is_ready, NULL);
}

/* Receive one byte; returns 0..255 or <0 on timeout/error. */
int th_get_byte(TilemCalc *c, int timeout_us)
{
	int v = -1, r = run_link(c, timeout_us, got_byte, &v);
	return r ? r : v;
}

void th_link_reset(TilemCalc *c) { tilem_linkport_graylink_reset(c); }

/* Fill out[96*64] with 0/1 pixels (1 = dark). */
void th_lcd(TilemCalc *c, unsigned char *out)
{
	TilemLCDBuffer *b = tilem_lcd_buffer_new();
	int x, y;
	tilem_lcd_get_frame1(c, b);
	for (y = 0; y < b->height && y < 64; y++)
		for (x = 0; x < b->width && x < 96; x++)
			out[y * 96 + x] = b->data[y * b->rowstride + x] ? 1 : 0;
	tilem_lcd_buffer_free(b);
}
int th_lcd_on(TilemCalc *c) { return c->lcd.active; }

/* Raw memory access by logical (Z80) address, current mapping. */
int th_read_mem(TilemCalc *c, int addr)
{ return c->hw.z80_rdmem(c, addr & 0xffff); }
int th_pc(TilemCalc *c) { return c->z80.r.pc.w.l; }
