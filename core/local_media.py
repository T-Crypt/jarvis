"""
Local Media Controller - Hooks into Windows Native Media Controls (SMTC)
Works with Spotify, Chrome, Edge, VLC, etc. Offline and local.
"""
import asyncio

class LocalMediaController:
    """Controls native Windows media playback without web APIs."""
    
    async def get_current_state(self):
        try:
            # DEFERRED IMPORT: Prevents fatal COM thread conflicts with PySide6
            from winsdk.windows.media.control import (
                GlobalSystemMediaTransportControlsSessionManager as MediaManager,
                GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus
            )
            
            manager = await MediaManager.request_async()
            session = manager.get_current_session()
            if not session:
                return None
            
            info = await session.try_get_media_properties_async()
            playback = session.get_playback_info()
            
            is_playing = playback.playback_status == PlaybackStatus.PLAYING
            
            return {
                "title": info.title,
                "artist": info.artist,
                "is_playing": is_playing
            }
        except Exception as e:
            return None

    async def toggle_play_pause(self):
        try:
            from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
            manager = await MediaManager.request_async()
            session = manager.get_current_session()
            if session:
                await session.try_toggle_play_pause_async()
        except: pass

    async def next_track(self):
        try:
            from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
            manager = await MediaManager.request_async()
            session = manager.get_current_session()
            if session:
                await session.try_skip_next_async()
        except: pass

    async def previous_track(self):
        try:
            from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
            manager = await MediaManager.request_async()
            session = manager.get_current_session()
            if session:
                await session.try_skip_previous_async()
        except: pass

# Global instance
local_media = LocalMediaController()