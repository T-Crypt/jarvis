"""
JARVIS Theme - Iron Man HUD aesthetic for Jarvis AI assistant.

Palette:
  #050a12  — void black (window bg)
  #0a1628  — deep navy (card surface)
  #0d1f3c  — elevated surface
  #00d4ff  — JARVIS cyan (primary accent)
  #0ea5c9  — cyan mid
  #ffd700  — gold (secondary accent)
  #ff3b30  — arc red (alerts)
  #c0c8d8  — primary text
  #6b7a95  — muted text
"""

JARVIS_STYLESHEET = """
/* ── Window & Layout ────────────────────────────────────────────── */

FluentWindow {
    background-color: #050a12;
    color: #c0c8d8;
}

StackedWidget {
    background-color: #050a12;
    border: none;
}

/* ── Navigation Sidebar ─────────────────────────────────────────── */

NavigationInterface {
    background-color: #070d1a;
    border-right: 1px solid rgba(0, 212, 255, 0.12);
}

NavigationWidget, NavigationPanel {
    background-color: #070d1a;
}

/* Navigation items */
NavigationPushButton, NavigationToolButton {
    color: #6b7a95;
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 8px;
}

NavigationPushButton:hover, NavigationToolButton:hover {
    color: #00d4ff;
    background-color: rgba(0, 212, 255, 0.08);
}

NavigationPushButton[selected=true], NavigationToolButton[selected=true] {
    color: #00d4ff;
    background-color: rgba(0, 212, 255, 0.12);
    border-left: 2px solid #00d4ff;
}

/* ── Cards ──────────────────────────────────────────────────────── */

CardWidget, SimpleCardWidget {
    background-color: #0a1628;
    border: 1px solid rgba(0, 212, 255, 0.12);
    border-radius: 14px;
}

CardWidget:hover, SimpleCardWidget:hover {
    border: 1px solid rgba(0, 212, 255, 0.25);
    background-color: #0d1f3c;
}

/* ── Typography ─────────────────────────────────────────────────── */

TitleLabel {
    color: #c0c8d8;
    font-family: "Segoe UI", "SF Pro Display", sans-serif;
    font-weight: 600;
}

SubtitleLabel {
    color: #c0c8d8;
    font-weight: 500;
}

StrongBodyLabel {
    color: #c0c8d8;
    font-weight: 600;
}

BodyLabel, CaptionLabel {
    color: #6b7a95;
}

/* ── Input Fields ───────────────────────────────────────────────── */

LineEdit, TextEdit, PlainTextEdit {
    background-color: #0a1628;
    border: 1px solid rgba(0, 212, 255, 0.2);
    border-radius: 10px;
    color: #c0c8d8;
    padding: 8px 12px;
    selection-background-color: rgba(0, 212, 255, 0.3);
}

LineEdit:focus, TextEdit:focus, PlainTextEdit:focus {
    border: 1px solid rgba(0, 212, 255, 0.6);
    background-color: #0d1f3c;
}

LineEdit::placeholder {
    color: #3a4a60;
}

/* ── Buttons ────────────────────────────────────────────────────── */

PrimaryPushButton {
    background-color: rgba(0, 212, 255, 0.15);
    border: 1px solid rgba(0, 212, 255, 0.5);
    border-radius: 8px;
    color: #00d4ff;
    font-weight: 600;
    padding: 8px 20px;
}

PrimaryPushButton:hover {
    background-color: rgba(0, 212, 255, 0.25);
    border: 1px solid #00d4ff;
}

PrimaryPushButton:pressed {
    background-color: rgba(0, 212, 255, 0.35);
}

PushButton {
    background-color: rgba(12, 25, 48, 0.9);
    border: 1px solid rgba(0, 212, 255, 0.2);
    border-radius: 8px;
    color: #c0c8d8;
    padding: 6px 16px;
}

PushButton:hover {
    background-color: rgba(0, 212, 255, 0.08);
    border: 1px solid rgba(0, 212, 255, 0.4);
    color: #00d4ff;
}

TransparentToolButton, TransparentPushButton {
    background-color: transparent;
    border: none;
    color: #6b7a95;
    border-radius: 6px;
}

TransparentToolButton:hover, TransparentPushButton:hover {
    color: #00d4ff;
    background-color: rgba(0, 212, 255, 0.08);
}

/* ── Scroll Bars ────────────────────────────────────────────────── */

QScrollBar:vertical {
    background: transparent;
    width: 4px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: rgba(0, 212, 255, 0.2);
    min-height: 20px;
    border-radius: 2px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(0, 212, 255, 0.5);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: transparent;
    height: 4px;
}

QScrollBar::handle:horizontal {
    background: rgba(0, 212, 255, 0.2);
    border-radius: 2px;
}

/* ── List & Session Sidebar ─────────────────────────────────────── */

ListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}

ListWidget::item {
    color: #6b7a95;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 2px 4px;
}

ListWidget::item:hover {
    background-color: rgba(0, 212, 255, 0.07);
    color: #c0c8d8;
}

ListWidget::item:selected {
    background-color: rgba(0, 212, 255, 0.14);
    color: #00d4ff;
    border-left: 2px solid #00d4ff;
}

/* ── Toggle / Switch ────────────────────────────────────────────── */

SwitchButton[checked=true] {
    background-color: rgba(0, 212, 255, 0.3);
    border: 1px solid #00d4ff;
}

/* ── Slider ─────────────────────────────────────────────────────── */

Slider::groove:horizontal {
    background: rgba(0, 212, 255, 0.15);
    height: 4px;
    border-radius: 2px;
}

Slider::handle:horizontal {
    background: #00d4ff;
    width: 14px;
    height: 14px;
    border-radius: 7px;
    margin: -5px 0;
}

Slider::sub-page:horizontal {
    background: rgba(0, 212, 255, 0.5);
    border-radius: 2px;
}

/* ── ComboBox ───────────────────────────────────────────────────── */

ComboBox {
    background-color: #0a1628;
    border: 1px solid rgba(0, 212, 255, 0.2);
    border-radius: 8px;
    color: #c0c8d8;
    padding: 6px 12px;
}

ComboBox:hover {
    border: 1px solid rgba(0, 212, 255, 0.4);
}

ComboBox QAbstractItemView {
    background-color: #0d1f3c;
    border: 1px solid rgba(0, 212, 255, 0.25);
    border-radius: 8px;
    color: #c0c8d8;
    selection-background-color: rgba(0, 212, 255, 0.2);
}

/* ── ToolTips ───────────────────────────────────────────────────── */

QToolTip {
    background-color: #0d1f3c;
    border: 1px solid rgba(0, 212, 255, 0.3);
    color: #c0c8d8;
    padding: 6px 10px;
    border-radius: 6px;
}

/* ── Title Bar ──────────────────────────────────────────────────── */

TitleBar {
    background-color: #050a12;
    border-bottom: 1px solid rgba(0, 212, 255, 0.1);
}

/* ── Settings ───────────────────────────────────────────────────── */

SettingCardGroup {
    background-color: transparent;
}

SettingCard {
    background-color: #0a1628;
    border: 1px solid rgba(0, 212, 255, 0.1);
    border-radius: 10px;
}

SettingCard:hover {
    border: 1px solid rgba(0, 212, 255, 0.25);
    background-color: #0d1f3c;
}

/* ── Info Bar / Toast ───────────────────────────────────────────── */

InfoBar {
    background-color: #0d1f3c;
    border: 1px solid rgba(0, 212, 255, 0.3);
    border-radius: 10px;
    color: #c0c8d8;
}

/* ── Scroll Area ────────────────────────────────────────────────── */

ScrollArea, QScrollArea {
    background-color: transparent;
    border: none;
}

/* ── Generic Containers ─────────────────────────────────────────── */

QWidget#chatContent, QWidget#plannerPanel,
QWidget#briefingView, QFrame#homeAutomationView,
QWidget#scrollWidget {
    background-color: transparent;
}

/* ── Dashboard specific ─────────────────────────────────────────── */

QWidget#dashboardView {
    background-color: transparent;
}

QFrame#hudCard {
    background-color: #0a1628;
    border: 1px solid rgba(0, 212, 255, 0.18);
    border-top: 1px solid rgba(0, 212, 255, 0.35);
    border-radius: 16px;
}

QFrame#statCard {
    background-color: #0a1628;
    border: 1px solid rgba(0, 212, 255, 0.14);
    border-radius: 14px;
}

QFrame#statCard:hover {
    border: 1px solid rgba(0, 212, 255, 0.35);
    background-color: #0d1f3c;
}

QFrame#goldCard {
    background-color: #0a1628;
    border: 1px solid rgba(255, 215, 0, 0.2);
    border-top: 1px solid rgba(255, 215, 0, 0.4);
    border-radius: 14px;
}

QFrame#alertCard {
    background-color: #0a1628;
    border: 1px solid rgba(255, 59, 48, 0.25);
    border-top: 1px solid rgba(255, 59, 48, 0.5);
    border-radius: 14px;
}
"""