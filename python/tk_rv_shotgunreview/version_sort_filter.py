# Copyright (c) 2016 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import tank

from tank.platform.qt import QtCore, QtGui

shotgun_model = tank.platform.import_framework(
    "tk-framework-shotgunutils",
    "shotgun_model",
)

shotgun_globals = tank.platform.import_framework(
    "tk-framework-shotgunutils",
    "shotgun_globals",
)

class VersionSortFilterProxyModel(QtGui.QSortFilterProxyModel):
    """
    A sort/filter proxy model that handles sorting and filtering
    data in a ShotgunModel by given Shotgun fields on the entities
    stored therein.

    :ivar filter_by_fields:     A list of string Shotgun field names to filter on.
    :ivar sort_by_fields:       A list of string Shotgun field names to sort by.
    :ivar primary_sort_field:   A string Shotgun field name that acts as the primary
                                field to sort on.
    """
    def __init__(self, parent, shotgun_field_manager=None):
        """
        Initializes a new VersionSortFilterProxyModel.

        :param parent:                  The Qt parent of the proxy model.
        :param shotgun_field_manager:   An option ShotgunFieldManager object, which will
                                        be used to aid in filtering against certain types
                                        of fields. If not provided, what is searched for
                                        those field types might not match what the user
                                        sees in the GUI.
        """
        super(VersionSortFilterProxyModel, self).__init__(parent)

        self.filter_by_fields = ["id"]
        self.sort_by_fields = ["id"]
        self.primary_sort_field = "id"
        self.shotgun_field_manager = shotgun_field_manager

    def lessThan(self, left, right):
        """
        Returns True if "left" is less than "right", otherwise
        False. This sort is handled based on the data pulled from
        Shotgun for the current sort_by_field registered with this
        proxy model.

        :param left:    The QModelIndex of the left-hand item to
                        compare.
        :param right:   The QModelIndex of the right-hand item to
                        compare against.
        """
        sg_left = shotgun_model.get_sg_data(left)
        sg_right = shotgun_model.get_sg_data(right)

        # Sorting by multiple columns, where each column is given a chance
        # to say that the items are out of order. This isn't a stable sort,
        # because we have no way of knowing the current position of left
        # and right in the list, and we have no way to tell Qt that they're
        # equal. That's going to be consistent across Qt, though, so nothing
        # we can/should do about it.
        #
        # We push the primary sort field to the beginning of the list of
        # fields that we're going to sort on, then least the rest in their
        # existing order to act as secondary sort fields.
        secondary_sort_fields = [f for f in self.sort_by_fields if f != self.primary_sort_field]

        # We are also going to shove "id" to the end of the secondary list
        # if it is present. This is because it will never be equal between
        # two entities, and thus will act as a wall to any secondary fields
        # we might want to sort by lower in the list. As such, we'll treat
        # it as the lowest priority.
        if "id" in secondary_sort_fields:
            secondary_sort_fields = [f for f in secondary_sort_fields if f != "id"] + ["id"]

        sort_fields = [self.primary_sort_field] + secondary_sort_fields

        for sort_by_field in sort_fields:
            try:
                left_data = self._get_processable_field_data(sg_left, sort_by_field)
                right_data = self._get_processable_field_data(sg_right, sort_by_field)
            except KeyError:
                continue

            if left_data == right_data:
                continue
            else:
                return (left_data < right_data)

        return False

    def filterAcceptsRow(self, row, source_parent):
        """
        Returns True if the model index should be shown, and False
        if it should not. This is determined based on whether the
        proxy model's filter is found in the Shotgun data for
        the fields specified in the filter_by_fields list registered
        with the proxy model.

        :param row:             The row being processed.
        :param source_parent:   The parent index from the source model.
        """
        if not self.filter_by_fields:
            return True

        # We only have one column, so column 0 is what we're
        # after.
        sg_data = shotgun_model.get_sg_data(
            self.sourceModel().index(row, 0, source_parent),
        )

        if not sg_data:
            return True

        for field in self.filter_by_fields:
            try:
                match_data = self._get_processable_field_data(sg_data, field)
            except KeyError:
                continue

            # No support for boolean fields.
            if isinstance(match_data, bool):
                continue

            # We'll make this a looser match by making it case insensitive
            # and bounding it with wildcards. This makes using the search
            # feature much more like a "search" and less like a regex
            # experiment.
            regex = self.filterRegExp()
            regex.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
            regex.setPattern("*%s*" % regex.pattern())

            if regex.exactMatch(str(match_data)):
                return True

        return False

    def _get_processable_field_data(self, sg_data, field):
        """
        For a given entity dictionary and field name, returns sortable
        and/or searchable data.

        :param sg_data: An entity dictionary.
        :param field:   A string Shotgun field to process.
        """
        data_type = shotgun_globals.get_data_type(
            self.sourceModel().get_entity_type(),
            field,
        )

        # Certain field data types will need to be treated specially
        # in order to properly search them. Those are handled here,
        # though it's possible additional types will need to be
        # specifically handled. Of the data types listed in the SG
        # Python API at the time of this writing, the below represents
        # those that will not stringify well for this purpose.
        if data_type == "entity":
            processable_data = sg_data[field]["name"]
        elif data_type == "status_list":
            status_name = shotgun_globals.get_status_display_name(sg_data[field])
            statuses = shotgun_globals.get_ordered_status_list(display_names=True)
            try:
                processable_data = statuses.index(status_name)
            except Exception:
                # This is unlikely to ever be the case unless there's
                # possibly a status cache sync issue, but if it does
                # we can just give it a number less than 0 so that a
                # status that we don't have information on will just
                # end up sorting before the others.
                processable_data = -1
        elif data_type == "multi_entity":
            processable_data = "".join([e.get("name", "") for e in sg_data[field]])
        elif data_type == "date_time":
            # Most likely what's being displayed is a field widget
            # out of the qtwidgets framework. The implementation there
            # has special logic for how to format the date_time data
            # that we want to match when searching. The easiest way
            # to do that is to just get a label and use its text. If
            # we don't have a field manager, we'll just end up stringifying
            # the datetime object that the API returns and using that.
            if self.shotgun_field_manager:
                processable_data = self.shotgun_field_manager.create_display_widget(
                    sg_entity_type=self.sourceModel().get_entity_type(),
                    field_name=field,
                    entity=sg_data,
                ).text()
            else:
                processable_data = sg_data[field]
        elif data_type == "tag_list":
            processable_data = "".join(sg_data[field])
        else:
            processable_data = sg_data[field]

        return processable_data
