from copy import deepcopy
from typing import List, Dict
from PySide2 import QtWidgets as qtw, QtCore as qtc

from Masa.core.data import Instance, TrackedObject
from Masa.core.utils import SignalPacket, DataUpdateInfo


class InstanceEditorDialog(qtw.QDialog):
    prop_data_change = qtc.Signal(SignalPacket)
    new = "NEW "

    def __init__(self, instance: Instance, obj_clsses_map: Dict[str, List[int]],
                 tags: Dict[str, List[str]], delete_btn=True, add_only=False,
                 parent=None):
        super().__init__(parent=parent, modal=True)
        self.instance = deepcopy(instance)
        self.obj_clsses_map = obj_clsses_map
        self.tags = tags
        self.new_t_id = sum([len(t_id) for t_id in self.obj_clsses_map.values()])
        self.delete_btn = delete_btn
        self.add_only = add_only

        self._set_widgets()
        self._optimize_widgets()
        self._set_layouts()
        self._init()

    def _set_widgets(self):
        # Track ID ############################################################
        # obj_cls = self.instance.object_class
        # ins_id = self.instance.instance_id
        # if obj_cls is None:
        #     obj_cls = list(self.obj_clsses_map.keys())[0]
        #     ins_id = None

        track_id_combo_box = qtw.QComboBox(editable=False)
        track_id_combo_box.addItems(
            [f"{self.new} Track ID"] + [str(i) for i in 
                self.obj_clsses_map[self.instance.object_class]]
        )
        track_id = (
            qtw.QLabel("Track ID"),
            track_id_combo_box
        )

        # Instance ID #########################################################
        instance_id = (
            qtw.QLabel("Instance ID"),
            qtw.QLabel(str(self.instance.instance_id))
        )

        self.loc_boxes = [track_id, instance_id]

        # Object Class ########################################################
        object_class_combo_box = qtw.QComboBox(editable=True,
                                               insertPolicy=qtw.QComboBox.InsertAtBottom)
        object_class_combo_box.addItems(
            [f"{self.new} Object Class"] + list(self.obj_clsses_map.keys())
        )
        object_class = (
            qtw.QLabel("Object Class"),
            object_class_combo_box
        )


        self.combo_boxes = {
            "object_class": object_class
        }

        for tag, vals in self.tags.items():
            combo_box = qtw.QComboBox(editable=True,
                                      insertPolicy=qtw.QComboBox.InsertAtBottom)
            combo_box.addItems([f"{self.new} {tag}", *vals])
            self.combo_boxes[tag] = (qtw.QLabel(tag), combo_box)

        self.btns = (qtw.QPushButton("Ok", clicked=self.accept),
                     qtw.QPushButton("Cancel", clicked=self.reject))
        if self.delete_btn:
            self.delete_btn = qtw.QPushButton("Delete", clicked=self.delete)

    def _optimize_widgets(self):
        # Set current `track_id`.
        # `instance_id` is set directly.
        # if self.instance:
        #     t_id = self.loc_boxes[0][1].findText(str(self.instance.track_id))
        #     obj_cls_idx = self.combo_boxes["object_class"][1].findText(self.instance.object_class)
        # else:
        #     t_id = 0
        #     obj_cls_idx = self.combo_boxes["object_class"][1].findText(
        #         list(self.obj_clsses_map.keys())[0])

        if self.instance.track_id is None:
            t_id = 0
        else:
            t_id = self.loc_boxes[0][1].findText(str(self.instance.track_id))

        self.loc_boxes[0][1].setCurrentIndex(t_id)

        # Set current `object_class` and connect it's signal.
        self.combo_boxes["object_class"][1].setCurrentIndex(
            self.combo_boxes["object_class"][1].findText(self.instance.object_class)
        )
        self.combo_boxes["object_class"][1].currentIndexChanged[str].connect(
            self._update_track_id_combo_box
        )

        # Set current `tags`.
        for key, (label, combo_box) in self.combo_boxes.items():
            if key == "object_class":
                continue
            if self.instance:
                combo_box.setCurrentIndex(
                    combo_box.findText(self.instance.tags.get(key, -1)))
            else:
                combo_box.setCurrentIndex(0)
            combo_box.model().item(0).setEnabled(True)

    def _update_track_id_combo_box(self, obj_cls):
        if obj_cls in self.obj_clsses_map.keys():
            items = [f"{self.new} Track ID"] + [str(i) for i in self.obj_clsses_map[obj_cls]]
        else:
            items = [str(self.new_t_id)]

        cb = self.loc_boxes[0][1]
        cb.clear()
        cb.addItems(items)

    def _set_layouts(self):
        self.setLayout(qtw.QFormLayout())

    def _init(self):
        for label, cb in self.loc_boxes:
            self.layout().addRow(label, cb)

        for label, widget in self.combo_boxes.values():
            self.layout().addRow(label, widget)

        self.layout().addRow(self.btns[0], self.btns[1])
        if self.delete_btn:
            self.layout().addRow(self.delete_btn)

    def delete(self):
        dui = DataUpdateInfo(
            deleted=(self.instance.track_id, self.instance.instance_id)
        )
        self.prop_data_change.emit(
            SignalPacket(sender=[self.__class__.__name__], data=dui)
        )
        super().accept()

    def _make_new_data(self):
        new_tobj = False
        if self.loc_boxes[0][1].currentIndex() == 0:
            # New TrackedObject.
            t_id = sum([len(t_id) for t_id in self.obj_clsses_map.values()])
            ins_id = 0
            new_tobj = True
        else:
            t_id = int(self.loc_boxes[0][1].currentText())
            if t_id == self.instance.track_id:
                # Same TrackedObject.
                ins_id = self.instance.instance_id
            else:
                # Different TrackedObject
                ins_id = -1

        obj_cls = self.combo_boxes["object_class"][1].currentText()
        obj_cls = (self.instance.object_class
                   if (obj_cls[:len(self.new)] == self.new or obj_cls == "")
                   else obj_cls)
        
        tags = {}
        for key, (label, combo_box) in self.combo_boxes.items():
            if key == "object_class":
                continue

            val = combo_box.currentText()
            val = None if (val[:len(self.new)] == self.new or val == "") else val
            tags[key] = val

        out = Instance(t_id, obj_cls, ins_id,
                       self.instance.x1, self.instance.y1,
                       self.instance.x2, self.instance.y2,
                       self.instance.frame_id, tags
        )
        if new_tobj:
            out = TrackedObject(t_id, obj_cls, out)

        return out

    def accept(self):
        data = self._make_new_data()

        if self.add_only:
            data.instance_id = -1
            dui = DataUpdateInfo(added=data)
        else:
            if isinstance(data, TrackedObject) or data.track_id != self.instance.track_id:
                dui = DataUpdateInfo(
                    moved=((self.instance.track_id, self.instance.instance_id), data)
                )
            else:
                dui = DataUpdateInfo(replaced=data)

        self.prop_data_change.emit(
            SignalPacket(sender=[self.__class__.__name__], data=dui)
        )

        super().accept()


if __name__ == "__main__":
    import sys

    app = qtw.QApplication(sys.argv)
    obj_cls_map = {"car": [1, 2, 4],
                   "truck": [3, 5, 6]}
    tags = {"view": "small medium big".split(), "time": "day night".split()}

    i_tags = {"view": "big", "time": "night"}
    instance = Instance(2, "car", 0, 1, 2, 1, 2, 3, i_tags)
    
    ad = InstanceEditorDialog(instance, obj_cls_map, tags)
    ad.show()
    sys.exit(app.exec_())

