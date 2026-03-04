import logging
import aiohttp

logger = logging.getLogger(__name__)
BASE = "https://api.uptimerobot.com/v2"


class UptimeRobotAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def _post(self, endpoint: str, payload: dict) -> dict | None:
        data = {**payload, "api_key": self.api_key, "format": "json"}
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(
                    f"{BASE}/{endpoint}",
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as r:
                    r.raise_for_status()
                    data = await r.json(content_type=None)
                    if data.get("stat") == "ok":
                        return data
                    logger.error("API error: %s", data)
                    return None
        except Exception as e:
            logger.error("Request failed: %s", e)
            return None

    # ── Account ───────────────────────────────────────────────────────────────
    async def get_account_details(self) -> dict | None:
        data = await self._post("getAccountDetails", {})
        return data.get("account") if data else None

    # ── Monitors ──────────────────────────────────────────────────────────────
    async def get_monitors(self, **kwargs) -> list:
        data = await self._post("getMonitors", dict(kwargs))
        return data.get("monitors", []) if data else []

    async def new_monitor(self, friendly_name: str, url: str, monitor_type: int, **kwargs) -> dict | None:
        payload = {"friendly_name": friendly_name, "url": url, "type": monitor_type, **kwargs}
        return await self._post("newMonitor", payload)

    async def edit_monitor(self, monitor_id: str, **kwargs) -> bool:
        data = await self._post("editMonitor", {"id": monitor_id, **kwargs})
        return data is not None

    async def delete_monitor(self, monitor_id: str) -> bool:
        data = await self._post("deleteMonitor", {"id": monitor_id})
        return data is not None

    async def reset_monitor(self, monitor_id: str) -> bool:
        data = await self._post("resetMonitor", {"id": monitor_id})
        return data is not None

    async def pause_monitor(self, monitor_id: str) -> bool:
        return await self.edit_monitor(monitor_id, status="0")

    async def resume_monitor(self, monitor_id: str) -> bool:
        return await self.edit_monitor(monitor_id, status="1")

    # ── Alert Contacts ────────────────────────────────────────────────────────
    async def get_alert_contacts(self) -> list:
        data = await self._post("getAlertContacts", {})
        return data.get("alert_contacts", []) if data else []

    async def new_alert_contact(self, contact_type: int, value: str, friendly_name: str = "") -> dict | None:
        payload = {"type": contact_type, "value": value}
        if friendly_name:
            payload["friendly_name"] = friendly_name
        return await self._post("newAlertContact", payload)

    async def edit_alert_contact(self, contact_id: str, friendly_name: str = "", value: str = "") -> bool:
        payload: dict = {"id": contact_id}
        if friendly_name:
            payload["friendly_name"] = friendly_name
        if value:
            payload["value"] = value
        data = await self._post("editAlertContact", payload)
        return data is not None

    async def delete_alert_contact(self, contact_id: str) -> bool:
        data = await self._post("deleteAlertContact", {"id": contact_id})
        return data is not None

    # ── Maintenance Windows ───────────────────────────────────────────────────
    async def get_mwindows(self) -> list:
        data = await self._post("getMWindows", {})
        return data.get("mwindows", []) if data else []

    async def new_mwindow(self, friendly_name: str, mw_type: int, value: str,
                          start_time: str, duration: int) -> dict | None:
        payload = {
            "friendly_name": friendly_name,
            "type": mw_type,
            "value": value,
            "start_time": start_time,
            "duration": duration,
        }
        return await self._post("newMWindow", payload)

    async def delete_mwindow(self, mwindow_id: str) -> bool:
        data = await self._post("deleteMWindow", {"id": mwindow_id})
        return data is not None

    # ── Public Status Pages ───────────────────────────────────────────────────
    async def get_psps(self) -> list:
        data = await self._post("getPSPs", {})
        return data.get("psps", []) if data else []

    async def new_psp(self, friendly_name: str, monitors: str = "0", **kwargs) -> dict | None:
        payload = {"friendly_name": friendly_name, "monitors": monitors, **kwargs}
        return await self._post("newPSP", payload)

    async def delete_psp(self, psp_id: str) -> bool:
        data = await self._post("deletePSP", {"id": psp_id})
        return data is not None
