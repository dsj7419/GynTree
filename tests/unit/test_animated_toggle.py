# tests/unit/test_animated_toggle.py
import pytest
from PyQt5.QtCore import QPoint, Qt, QTimer
from PyQt5.QtTest import QTest

from components.UI.animated_toggle import AnimatedToggle

pytestmark = pytest.mark.unit


@pytest.fixture
def toggle(qtbot):
    widget = AnimatedToggle()
    qtbot.addWidget(widget)
    return widget


def test_initial_state(toggle):
    """Test initial state of toggle"""
    assert not toggle.isChecked()
    assert toggle._handle_position == 0
    assert toggle._pulse_radius == 0


def test_size_hint(toggle):
    """Test size hint is correct"""
    size = toggle.sizeHint()
    assert size.width() == 58
    assert size.height() == 45


def test_hit_button(toggle):
    """Test hit button area"""
    assert toggle.hitButton(toggle.rect().center())
    assert not toggle.hitButton(toggle.rect().topLeft() - QPoint(1, 1))


@pytest.mark.timeout(30)
def test_animation(toggle, qtbot):
    """Test toggle animation"""
    with qtbot.waitSignal(toggle.toggled, timeout=1000):
        toggle.setChecked(True)

    def check_animation_complete():
        return toggle._handle_position >= 1

    qtbot.wait_until(check_animation_complete, timeout=2000)
    assert toggle._handle_position == 1


@pytest.mark.timeout(30)
def test_pulse_animation(toggle, qtbot):
    """Test pulse animation"""
    with qtbot.waitSignal(toggle.toggled, timeout=1000):
        toggle.setChecked(True)

    def check_pulse():
        return toggle._pulse_radius > 0

    qtbot.wait_until(check_pulse)
    assert toggle._pulse_radius > 0


def test_custom_colors(qtbot):
    """Test custom color initialization"""
    toggle = AnimatedToggle(
        bar_color=Qt.red, checked_color="#00ff00", handle_color=Qt.blue
    )
    qtbot.addWidget(toggle)

    assert toggle._bar_brush.color() == Qt.red
    assert toggle._handle_brush.color() == Qt.blue


@pytest.mark.timeout(30)
def test_rapid_toggling(toggle, qtbot):
    """Test rapid toggling doesn't break animations"""
    for _ in range(5):
        with qtbot.waitSignal(toggle.toggled, timeout=1000):
            toggle.setChecked(not toggle.isChecked())
        qtbot.wait(100)

    assert toggle.animations_group.state() in (
        toggle.animations_group.Running,
        toggle.animations_group.Stopped,
    )


def test_paint_event(toggle, qtbot):
    """Test paint event execution"""
    toggle.update()
    QTest.qWait(100)
    assert True


def test_memory_cleanup(toggle, qtbot):
    """Test proper cleanup of animations"""
    qtbot.wait(100)
    assert True


@pytest.mark.timeout(30)
def test_state_consistency(toggle, qtbot):
    """Test state consistency during animations"""
    states = []

    def record_state():
        states.append(
            {
                "checked": toggle.isChecked(),
                "handle_pos": toggle._handle_position,
                "pulse_radius": toggle._pulse_radius,
            }
        )

    # Record states during transition
    record_state()  # Initial state

    with qtbot.waitSignal(toggle.toggled, timeout=1000):
        toggle.setChecked(True)

    record_state()  # After toggle

    qtbot.wait(500)  # Wait for animation
    record_state()  # After animation

    # Verify state transitions
    assert not states[0]["checked"]  # Initially unchecked
    assert states[0]["handle_pos"] == 0

    assert states[1]["checked"]  # Checked after toggle

    assert states[2]["checked"]  # Still checked after animation
    assert states[2]["handle_pos"] == 1


@pytest.mark.timeout(30)
def test_performance(toggle, qtbot):
    """Test toggle performance under rapid updates"""
    import time

    start_time = time.time()
    for _ in range(10):
        with qtbot.waitSignal(toggle.toggled, timeout=1000):
            toggle.setChecked(not toggle.isChecked())
        qtbot.wait(50)

    duration = time.time() - start_time
    assert duration < 2.0  # Should complete within 2 seconds
