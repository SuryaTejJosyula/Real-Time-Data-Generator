"""
BounceButton — QPushButton with elastic press animation.
"""

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import (
    QPropertyAnimation, QSequentialAnimationGroup,
    QEasingCurve, QRect, QAbstractAnimation
)


class BounceButton(QPushButton):
    """
    A QPushButton that plays a squeeze-and-bounce animation on click.
    Works by briefly shrinking the widget geometry and then springing back
    with an OutElastic easing curve.
    """

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._play_bounce()

    def _play_bounce(self):
        geom: QRect = self.geometry()
        cx = geom.x() + geom.width() // 2
        cy = geom.y() + geom.height() // 2

        shrink_px = max(4, int(min(geom.width(), geom.height()) * 0.06))

        squeezed = QRect(
            cx - (geom.width() // 2 - shrink_px),
            cy - (geom.height() // 2 - shrink_px),
            geom.width() - shrink_px * 2,
            geom.height() - shrink_px * 2,
        )

        # Squeeze in
        anim_in = QPropertyAnimation(self, b"geometry")
        anim_in.setDuration(60)
        anim_in.setStartValue(geom)
        anim_in.setEndValue(squeezed)
        anim_in.setEasingCurve(QEasingCurve.Type.OutQuad)

        # Bounce back
        anim_out = QPropertyAnimation(self, b"geometry")
        anim_out.setDuration(380)
        anim_out.setStartValue(squeezed)
        anim_out.setEndValue(geom)
        anim_out.setEasingCurve(QEasingCurve.Type.OutElastic)

        group = QSequentialAnimationGroup(self)
        group.addAnimation(anim_in)
        group.addAnimation(anim_out)
        group.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
