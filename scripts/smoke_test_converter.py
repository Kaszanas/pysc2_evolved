"""Smoke test: verify pybind11 extensions are importable and execute C++ code."""
from pysc2_evolved.env.converter.cc.python import converter
from pysc2_evolved.env.converter.cc.game_data.python import uint8_lookup

assert hasattr(converter, "Converter"), "converter.Converter missing"
assert hasattr(converter, "MakeConverter"), "converter.MakeConverter missing"

max_unit = uint8_lookup.MaximumUnitTypeId()
max_buff = uint8_lookup.MaximumBuffId()
assert isinstance(max_unit, int) and max_unit > 0, f"unexpected MaximumUnitTypeId: {max_unit}"
assert isinstance(max_buff, int) and max_buff > 0, f"unexpected MaximumBuffId: {max_buff}"

print(f"converter    OK  Converter={converter.Converter}  MakeConverter={converter.MakeConverter}")
print(f"uint8_lookup OK  MaximumUnitTypeId={max_unit}  MaximumBuffId={max_buff}")
