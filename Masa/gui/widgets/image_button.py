from PySide2 import QtWidgets as qtw, QtGui as qtg, QtCore as qtc
import cv2
import numpy as np

from Masa.core.utils import convert_np, resize_calculator, SignalPacket


class QPushImageButton(qtw.QPushButton):
    """A `QPushButton` that supports left and right mouse click."""
    right_clicked = qtc.Signal()
    left_clicked = qtc.Signal()
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def mousePressEvent(self, event):
        if event.button() == qtc.Qt.RightButton:
            self.right_clicked.emit()
        elif event.button() == qtc.Qt.LeftButton:
            self.left_clicked.emit()


class ImageButton(qtw.QWidget):
    """A widget that represents a `QPushImageButton` with label at its bottom."""
    i_id_template = "<b>Instance ID<\b>: {}"
    left_clicked = qtc.Signal(SignalPacket)
    right_clicked = qtc.Signal(SignalPacket)
    def __init__(self,
                 track_id, instance_id, frame_id,
                 x1, y1, x2, y2, meta,
                 parent=None,
                 image: np.ndarray = None,
                 width=100, height=100):
        super().__init__(parent=parent)
        self.track_id = track_id
        self.frame_id = frame_id
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.meta = meta
        self.width = width
        self.height = height

        image_btn = QPushImageButton()
        info_label = qtw.QLabel()
        image_btn.left_clicked.connect(self._left_clicked)
        image_btn.right_clicked.connect(self._right_clicked)

        self.setLayout(qtw.QBoxLayout(qtw.QBoxLayout.TopToBottom))
        self.layout().setSpacing(1)
        self.layout().addWidget(image_btn)
        self.layout().addWidget(info_label)

        if image is None:
            image = np.zeros([self.height, self.width, 3], dtype=np.uint8)
        self.set_np(image)
        self.set_instance_id(instance_id)

    def _left_clicked(self):
        self.left_clicked.emit(
            SignalPacket(sender=self.__class__.__name__,
                         data=self.frame_id)
        )

    def _right_clicked(self):
        self.right_clicked.emit(
            SignalPacket(sender=self.__class__.__name__,
                         data=(self.track_id, self.instance_id))
        )

    def sizeHint(self):
        ib_size = self.layout().itemAt(0).widget().size()
        il_size = self.layout().itemAt(1).widget().size()

        height = ib_size.height() + il_size.height()
        return qtc.QSize(max(ib_size.width(), il_size.width()), height)

    def set_np(self, image: np.ndarray):
        image_btn = self.layout().itemAt(0).widget()
        height, width = image.shape[:2]
        if width >= height:
            kwargs = {"target_width": self.width}
        else:
            kwargs = {"target_height": self.height}

        width, height = resize_calculator(width, height, **kwargs)
        image = cv2.resize(
            image, (width, height), interpolation=cv2.INTER_CUBIC
        )
        canvas = np.zeros([self.height, self.width, 3], np.uint8)
        if width == self.width:
            entry_y = (self.height - height) // 2
            canvas[entry_y:entry_y + height, ...] = image
        else:
            entry_x = (self.width - width) // 2
            canvas[:, entry_x:entry_x + width, ...] = image

        # XXX: Weird, sometimes, even if `input_bgr` is False, it is still
        #      output OK.
        image = convert_np(canvas, to="qpixmap")
        frame_icon = qtg.QIcon(image)
        image_btn.setIcon(frame_icon)

        image_btn.setIconSize(qtc.QSize(self.width, self.height))
        image_btn.setFixedSize(self.width, self.height)

    def set_instance_id(self, instance_id):
        self.instance_id = instance_id
        info_label = self.layout().itemAt(1).widget()
        info_label.setText(self.i_id_template.format(str(self.instance_id)))


if __name__ == '__main__':
    import sys
    # Import mock data for visualization
    from Masa.tests.utils import DummyAnnotationsFactory, DummyBufferFactory
    import cv2

    anno = DummyAnnotationsFactory.get_annotations("simple_anno")
    video = DummyBufferFactory.get_buffer("ocv_simple_tagged", length=100)
    h = anno.head

    app = qtw.QApplication(sys.argv)
    window = qtw.QWidget()
    window.setLayout(qtw.QVBoxLayout())

    max_show = 3
    for idx, object_id in enumerate(anno.data_per_object_id):
        # We want only show three rows of track_id.
        if idx >= max_show:
            break

        # Every instance from a specific track_id will be shown horizontally.
        h_layout = qtw.QHBoxLayout()
        for i, instance in enumerate(object_id):
            # Per instance_id of the track_id.
            # Get needed information.
            f_id = instance[h.index("frame_id")]
            x1=instance[h.index("x1")]
            y1=instance[h.index("y1")]
            x2=instance[h.index("x2")]
            y2=instance[h.index("y2")]

            # Get frame and crop it based on the annotations.
            video.set(cv2.CAP_PROP_POS_FRAMES, f_id)
            ret, frame = video.read()
            cropped = frame[y1:y2 + 1, x1:x2 + 1]

            # The image button should resize the image appropriately.
            img_btn = ImageButton(
                track_id=instance[h.index("track_id")], instance_id=i,
                frame_id=f_id,
                x1=x1 / video.width,
                y1=y1 / video.height,
                x2=x2 / video.width,
                y2=y2 / video.height,
                meta=None,
                image=cropped
            )
            h_layout.addWidget(img_btn)

        window.layout().addLayout(h_layout)
    window.show()

    sys.exit(app.exec_())
