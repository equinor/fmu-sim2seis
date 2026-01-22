# Settings to include in script that is controlled by debug server
#
import debugpy

debugpy.listen(("localhost", 5678))
print("⏸ Waiting for debugger to attach on port 5678...")
debugpy.wait_for_client()
print("✓ Debugger attached!")
debugpy.breakpoint()
