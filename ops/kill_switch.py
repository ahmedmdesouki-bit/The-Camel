"""Founder kill switch (stub). Halts NEW actions; never auto-liquidates (no panic selling)."""
import sys, pathlib
FLAG = pathlib.Path(__file__).resolve().parent.parent / "config" / "HALT"
def halt():  FLAG.write_text("halted\n"); print("Camel halted — no new actions will run.")
def resume(): FLAG.unlink(missing_ok=True); print("Camel resumed.")
def is_halted() -> bool: return FLAG.exists()
if __name__ == "__main__":
    {"halt": halt, "resume": resume}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print("usage: kill_switch.py halt|resume"))()
