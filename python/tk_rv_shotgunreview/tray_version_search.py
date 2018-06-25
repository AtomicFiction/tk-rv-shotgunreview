
import sgtk

from sgtk.platform.qt import QtCore, QtGui

shotgun_model = sgtk.platform.import_framework(
    "tk-framework-shotgunutils",
    "shotgun_model",
)

proxy_models = sgtk.platform.import_framework(
    "tk-framework-qtwidgets",
    "models",
)

search_widget = sgtk.platform.import_framework(
    "tk-framework-qtwidgets",
    "search_widget",
)

hierarchical_proxy = proxy_models.hierarchical_filtering_proxy_model

class VersionTreeProxyModel(hierarchical_proxy.HierarchicalFilteringProxyModel):

    def __init__(self, parent=None):
        super(VersionTreeProxyModel, self).__init__(parent=parent)

    def _is_row_accepted(self, src_row, src_parent_idx, parent_accepted):

        if not parent_accepted:
            return True

        model = self.sourceModel()

        version_code = model.data(model.index(src_row, 0, src_parent_idx))
        code_matches = self.filterRegExp().exactMatch(version_code)

        return code_matches

class VersionSearchMenu(QtGui.QMenu):

    version_selected = QtCore.Signal(list)

    FIELDS = ['sg_uploaded_movie_frame_rate',
              'sg_first_frame',
              'sg_last_frame',
              'sg_movie_has_slate',
              'entity']

    # by default, never retrieve versions that don't have a step,
    # first/last frame, and/or path_to_movie set
    # (a lack of path_to_movie or first/last frame will cause the version
    # to not cut in correctly, and editorial requested to exclude any
    # versions without a step)
    FILTERS = [['sg_path_to_movie', 'is_not', None],
               ['sg_step.Step.sg_hide_from_sg_review', 'is_not', True],
               ['sg_first_frame', 'is_not', None],
               ['sg_last_frame', 'is_not', None],
               ['sg_step', 'is_not', None]]

    def __init__(self, parent=None, engine=None):
        QtGui.QMenu.__init__(self, parent)

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        self._main_layout = QtGui.QVBoxLayout()
        self._search_layout = QtGui.QHBoxLayout()
        self._version_layout = QtGui.QHBoxLayout()

        self._search_widget = search_widget.SearchWidget(self)
        self._search_layout.addWidget(self._search_widget)

        self._version_view = QtGui.QTreeView(self)
        self._version_proxy = VersionTreeProxyModel(self._version_view)
        self.version_model = shotgun_model.ShotgunModel(self._version_view,
                                                        download_thumbs=False,
                                                        bg_load_thumbs=False)

        self._version_proxy.setFilterWildcard('*')
        self._version_proxy.setSourceModel(self.version_model)
        self._version_view.setModel(self._version_proxy)
        self._version_layout.addWidget(self._version_view)

        self._main_layout.addLayout(self._search_layout)
        self._main_layout.addLayout(self._version_layout)

        self.setLayout(self._main_layout)

        self.setMinimumWidth(500)
        self.setMinimumHeight(500)

        '''
        Maybe #TODO pending user feedback:
        - Automatically expand all tree contents when data reloads
        - Set menu size based on model contents
        - Do we need to deal with users wanting sg_frames instead of sg_path_to_movie?
        - When searching via proxy, hide tree items that have no children
        '''

    def _connect_signals(self):
        # tell the proxy to update its search as the user types and whenever
        # the user hits 'enter'
        self._search_widget.search_edited.connect(self._set_proxy_regex)
        self._search_widget.search_changed.connect(self._set_proxy_regex)

        self._version_view.doubleClicked.connect(self._version_selected)

    def _set_proxy_regex(self, search_args):
        self._version_proxy.invalidateFilter()
        regex = '*{args}*'.format(args=search_args)
        self._version_proxy.setFilterWildcard(regex)
        self._version_proxy.invalidateFilter()

    def _version_selected(self, event):
        item = self.version_model.itemFromIndex(self._version_proxy.mapToSource(event))
        sg_data = item.get_sg_data()

        if not sg_data:
            return

        # since this is only being used in tk-rv-shotgunreview, we want to leverage
        # that plugin's existing _swap_into_sequence, which expects to receive
        # a list of versions; so we'll emit a list, even though we only have one
        # version to swap in
        self.version_selected.emit([sg_data])

        self.close()

    def load(self, version, filters):
        """
        Given a version, load associated versions into the VersionSearchMenu.

        :param version dict: Version entity to find associated Versions for.
        :param filters list: List of Shotgun query filters. Typically this
            should contain the version's project and entity, so that the
            model only loads versions from the correct show/entity.
        """

        filters.extend(self.FILTERS)

        self.version_model._load_data('Version',
                                      filters,
                                      ['sg_step', 'code'],
                                      self.FIELDS)

        self.version_model._refresh_data()

        self._version_proxy.invalidateFilter()
        self._version_proxy.setFilterWildcard('*')
        self._version_proxy.sort(0, QtCore.Qt.DescendingOrder)
