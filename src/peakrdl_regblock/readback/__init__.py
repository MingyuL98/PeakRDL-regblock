from typing import TYPE_CHECKING
import math

from .generators import ReadbackAssignmentGenerator
from ..utils import get_always_ff_event

if TYPE_CHECKING:
    from ..exporter import RegblockExporter
    from systemrdl.node import AddrmapNode

class Readback:
    def __init__(self, exp:'RegblockExporter', do_fanin_stage: bool):
        self.exp = exp
        self.do_fanin_stage = do_fanin_stage

    @property
    def top_node(self) -> 'AddrmapNode':
        return self.exp.top_node

    def get_implementation(self) -> str:
        gen = ReadbackAssignmentGenerator(self.exp)
        array_assignments = gen.get_content(self.top_node)
        array_size = gen.current_offset

        # Enabling the fanin stage doesnt make sense if readback fanin is
        # small. This also avoids pesky corner cases
        if array_size < 4:
            self.do_fanin_stage = False

        context = {
            "array_assignments" : array_assignments,
            "array_size" : array_size,
            "get_always_ff_event": lambda resetsignal : get_always_ff_event(self.exp.dereferencer, resetsignal),
            "cpuif": self.exp.cpuif,
            "do_fanin_stage": self.do_fanin_stage,
        }

        if self.do_fanin_stage:
            # If adding a fanin pipeline stage, goal is to try to
            # split the fanin path in the middle so that fanin into the stage
            # and the following are roughly balanced.
            fanin_target = math.sqrt(array_size)

            # Size of fanin group to consume per fanin element
            fanin_stride = math.floor(fanin_target)

            # Number of array elements to reduce to.
            # Round up to an extra element in case there is some residual
            fanin_array_size = math.ceil(array_size / fanin_stride)

            # leftovers are handled in an extra array element
            fanin_residual_stride = array_size % fanin_stride

            if fanin_residual_stride != 0:
                # If there is a partial fanin element, reduce the number of
                # loops performed in the bulk fanin stage
                fanin_loop_iter = fanin_array_size - 1
            else:
                fanin_loop_iter = fanin_array_size

            context['fanin_stride'] = fanin_stride
            context['fanin_array_size'] = fanin_array_size
            context['fanin_residual_stride'] = fanin_residual_stride
            context['fanin_loop_iter'] = fanin_loop_iter

        template = self.exp.jj_env.get_template(
            "readback/templates/readback.sv"
        )
        return template.render(context)
