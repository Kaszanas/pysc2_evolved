"""Smoke test: verify pybind11 extensions and protobuf modules are importable."""
from pysc2_evolved.env.converter.cc.python import converter
from pysc2_evolved.env.converter.cc.game_data.python import uint8_lookup
from pysc2_evolved.env.converter.proto import converter_pb2
from pysc2_evolved.env.converter.converter import Converter

assert hasattr(converter, "Converter"), "converter.Converter missing"
assert hasattr(converter, "MakeConverter"), "converter.MakeConverter missing"

max_unit = uint8_lookup.MaximumUnitTypeId()
max_buff = uint8_lookup.MaximumBuffId()
assert isinstance(max_unit, int) and max_unit > 0, f"unexpected MaximumUnitTypeId: {max_unit}"
assert isinstance(max_buff, int) and max_buff > 0, f"unexpected MaximumBuffId: {max_buff}"

assert hasattr(converter_pb2, "ConverterSettings"), "converter_pb2.ConverterSettings missing"
assert hasattr(converter_pb2, "EnvironmentInfo"), "converter_pb2.EnvironmentInfo missing"

print(f"converter    OK  Converter={converter.Converter}  MakeConverter={converter.MakeConverter}")
print(f"uint8_lookup OK  MaximumUnitTypeId={max_unit}  MaximumBuffId={max_buff}")
print(f"converter_pb2 OK  ConverterSettings={converter_pb2.ConverterSettings}")
print(f"Converter    OK  {Converter}")
