"""
Grouping functionality allows to nest one item within another item (parent
item). This is useful in several use cases

- artifact deployed within a node
- a class within a package or a component
- composite structures (i.e. component within a node)

The grouping adapters has to implement three methods, see `AbstractGroup`
class.

It is important to note, that grouping adapters can be queried before
instance of an item to be grouped is created. This happens when item
is about to be created. Therefore `AbstractGroup.can_contain` has
to be aware that `AbstractGroup.item` can be null.
"""
import logging
import abc

from zope.interface import implementer
from zope import component

from gaphor import UML
from gaphor.core import inject
from gaphor.diagram import items
from gaphor.diagram.interfaces import Group

log = logging.getLogger(__name__)


# TODO: I think this should have been called Namespacing or something similar,
# since that's the modeling concept.
class AbstractGroup(metaclass=abc.ABCMeta):
    """
    Base class for grouping UML objects, i.e.
    interactions contain lifelines and components contain classes objects.

    Base class for grouping UML objects.

    :Attributes:
     parent
        Parent item, which groups other items.
     item
        Item to be grouped.
    """

    element_factory = inject("element_factory")

    def __init__(self, parent, item):
        self.parent = parent
        self.item = item

    def can_contain(self):
        """
        Determine if parent can contain item.
        """
        return True

    @abc.abstractmethod
    def group(self):
        """
        Perform grouping of items.
        """

    @abc.abstractmethod
    def ungroup(self):
        """
        Perform ungrouping of items.
        """


# Until we can deal with types (esp. typing.Any) we use this as a workaround:
@Group.register(None, object)
class NoParentGroup(AbstractGroup):
    def group(self):
        pass

    def ungroup(self):
        pass


@Group.register(items.InteractionItem, items.LifelineItem)
class InteractionLifelineGroup(AbstractGroup):
    """
    Add lifeline to interaction.
    """

    def group(self):
        self.parent.subject.lifeline = self.item.subject
        self.parent.canvas.reparent(self.item, self.parent)

    def ungroup(self):
        del self.parent.subject.lifeline[self.item.subject]


@Group.register(items.NodeItem, items.NodeItem)
class NodeGroup(AbstractGroup):
    """
    Add node to another node.
    """

    def group(self):
        self.parent.subject.nestedNode = self.item.subject

    def ungroup(self):
        del self.parent.subject.nestedNode[self.item.subject]


@Group.register(items.NodeItem, items.ComponentItem)
class NodeComponentGroup(AbstractGroup):
    """
    Add components to node using internal structures.
    """

    def group(self):
        node = self.parent.subject
        component = self.item.subject

        # node attribute
        a1 = self.element_factory.create(UML.Property)
        a1.aggregation = "composite"
        # component attribute
        a2 = self.element_factory.create(UML.Property)

        e1 = self.element_factory.create(UML.ConnectorEnd)
        e2 = self.element_factory.create(UML.ConnectorEnd)

        # create connection between node and component
        e1.role = a1
        e2.role = a2
        connector = self.element_factory.create(UML.Connector)
        connector.end = e1
        connector.end = e2

        # compose component within node
        node.ownedAttribute = a1
        node.ownedConnector = connector
        component.ownedAttribute = a2

    def ungroup(self):
        node = self.parent.subject
        component = self.item.subject
        for connector in node.ownedConnector:
            e1 = connector.end[0]
            e2 = connector.end[1]
            if e1.role in node.ownedAttribute and e2.role in component.ownedAttribute:
                e1.role.unlink()
                e2.role.unlink()
                e1.unlink()
                e2.unlink()
                connector.unlink()
                log.debug("Removed %s from node %s" % (component, node))


@Group.register(items.NodeItem, items.ArtifactItem)
class NodeArtifactGroup(AbstractGroup):
    """
    Deploy artifact on node.
    """

    def group(self):
        node = self.parent.subject
        artifact = self.item.subject

        # deploy artifact on node
        deployment = self.element_factory.create(UML.Deployment)
        node.deployment = deployment
        deployment.deployedArtifact = artifact

    def ungroup(self):
        node = self.parent.subject
        artifact = self.item.subject
        for deployment in node.deployment:
            if deployment.deployedArtifact[0] is artifact:
                deployment.unlink()
                log.debug("Removed %s from node %s" % (artifact, node))


@Group.register(items.SubsystemItem, items.UseCaseItem)
class SubsystemUseCaseGroup(AbstractGroup):
    """
    Make subsystem a subject of an use case.
    """

    def group(self):
        component = self.parent.subject
        usecase = self.item.subject
        usecase.subject = component

    def ungroup(self):
        component = self.parent.subject
        usecase = self.item.subject
        usecase.subject.remove(component)


@Group.register(items.PartitionItem, items.PartitionItem)
class ActivityPartitionsGroup(AbstractGroup):
    """
    Group activity partitions.
    """

    def can_contain(self):
        return not self.parent.subject or (
            self.parent.subject and len(self.parent.subject.node) == 0
        )

    def group(self):
        p = self.parent.subject
        sp = self.element_factory.create(UML.ActivityPartition)
        self.item.subject = sp
        sp.name = "Swimlane"
        if p:
            p.subpartition = sp
        for k in self.item.canvas.get_children(self.item):
            sp.subpartition = k.subject

    def ungroup(self):
        p = self.parent.subject
        sp = self.item.subject
        if p:
            p.subpartition.remove(sp)
        self.item.subject = None
        for s in sp.subpartition:
            sp.subpartition.remove(s)
        assert len(sp.node) == 0

        # ungroup activity nodes
        canvas = self.item.canvas
        nodes = [
            n
            for n in canvas.get_children(self.item)
            if isinstance(
                n,
                (
                    items.ActivityNodeItem,
                    items.ActionItem,
                    items.ObjectNodeItem,
                    items.ForkNodeItem,
                ),
            )
        ]
        for n in nodes:
            canvas.reparent(n, None)

        sp.unlink()


class ActivityNodePartitionGroup(AbstractGroup):
    """
    Group activity nodes within activity partition.
    """

    def can_contain(self):
        return self.parent.subject and len(self.parent.subject.subpartition) == 0

    def group(self):
        partition = self.parent.subject
        node = self.item.subject
        partition.node = node

    def ungroup(self):
        partition = self.parent.subject
        node = self.item.subject
        partition.node.remove(node)


Group.register(items.PartitionItem, items.ActivityNodeItem)(ActivityNodePartitionGroup)
Group.register(items.PartitionItem, items.ActionItem)(ActivityNodePartitionGroup)
Group.register(items.PartitionItem, items.ObjectNodeItem)(ActivityNodePartitionGroup)
Group.register(items.PartitionItem, items.ForkNodeItem)(ActivityNodePartitionGroup)
