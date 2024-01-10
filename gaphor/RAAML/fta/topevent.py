"""Top Event item definition."""

from gaphas.geometry import Rectangle

from gaphor.core.modeling import DrawContext
from gaphor.diagram.presentation import (
    Classified,
    ElementPresentation,
    text_from_package,
    text_name,
)
from gaphor.diagram.shapes import Box, Text, draw_border
from gaphor.diagram.support import represents
from gaphor.RAAML import raaml
from gaphor.UML.recipes import stereotypes_str


@represents(raaml.TopEvent)
class TopEventItem(Classified, ElementPresentation):
    def __init__(self, diagram, id=None):
        super().__init__(diagram, id)

        self.watch("subject[NamedElement].name").watch(
            "subject[NamedElement].namespace.name"
        )

    def update_shapes(self, event=None):
        self.shape = Box(
            Box(
                Text(
                    text=lambda: stereotypes_str(
                        self.subject, [self.diagram.gettext("Top Event")]
                    ),
                ),
                text_name(self),
                text_from_package(self),
                style={"padding": (12, 4, 12, 4)},
            ),
            draw=draw_top_event,
        )


def draw_top_event(box, context: DrawContext, bounding_box: Rectangle):
    draw_border(box, context, bounding_box)
