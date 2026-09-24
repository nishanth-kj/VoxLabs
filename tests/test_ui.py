"""Smoke tests: the main window builds and every page can refresh (offscreen Qt)."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")


@pytest.fixture
def window(qtbot):
    from app.ui.main_window import MainWindow

    from PySide6.QtCore import QThreadPool

    from app.ui.widgets.progress import JobBridge

    win = MainWindow()
    qtbot.addWidget(win)
    yield win
    QThreadPool.globalInstance().waitForDone(10_000)
    qtbot.wait(50)  # deliver queued callbacks before the data directory goes away
    JobBridge.detach()


def test_every_page_opens(window, qtbot):
    for key in window.pages:
        window.go(key)
        assert window.stack.currentWidget() is window.pages[key]
    qtbot.wait(200)


def test_editor_undo_redo(window, voice_wav, qtbot):
    from app.services.audio_service import audio_service

    audio = audio_service.import_file(voice_wav)
    editor = window.pages["editor"]
    editor.open_audio(audio["audios_id"])
    qtbot.waitUntil(lambda: editor.audio is not None, timeout=5000)
    editor.waveform.select(1.0, 2.0)
    editor.delete()
    assert editor.waveform.duration == pytest.approx(3.0, abs=0.01)
    editor.undo()
    assert editor.waveform.duration == pytest.approx(4.0, abs=0.01)
    editor.redo()
    assert editor.ops[-1]["op"] == "delete"


def test_clone_button_requires_consent(window):
    page = window.pages["clone"]
    page.samples = [{"path": "x.wav", "analysis": {"ok": True, "errors": [], "issues": []}}]
    page.granted_by.setText("Operator")
    page.speaker.setText("Speaker")
    page._update_buttons()
    assert not page.clone_button.isEnabled()
    page.confirm.setChecked(True)
    assert page.clone_button.isEnabled()
