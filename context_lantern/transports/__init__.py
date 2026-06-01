"""Transport layer — OS x Host specific execution recipes.

Transport solves "make the process run to completion on a given OS",
not business logic. Things like:
- Windows .cmd wrappers
- stdin relay via temp files
- Python path resolution
- hooks.json command generation
"""
