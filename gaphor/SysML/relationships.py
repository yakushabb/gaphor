from gaphor.diagram.presentation import LinePresentation, Named, text_name
from gaphor.diagram.shapes import Box, draw_arrow_head
from gaphor.UML.compartments import text_stereotypes


class DirectedRelationshipPropertyPathItem(Named, LinePresentation):
    relation_type = ""

    def __init__(self, diagram, id=None):
        super().__init__(
            diagram,
            id,
            shape_middle=Box(
                text_stereotypes(self, lambda: [self.relation_type]),
                text_name(self),
            ),
        )

        self.draw_head = draw_arrow_head
        self.watch("subject[NamedElement].name").watch(
            "subject.appliedStereotype.classifier.name"
        )
