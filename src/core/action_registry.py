"""Eylem yürütme ve eşleştirme modülü.

Kullanıcının girdiği sayılara karşılık gelen sistem komutlarını,
web adreslerini veya özel fonksiyonları çalıştırır.
"""

import os
import subprocess
import webbrowser
from typing import Any, Callable, Dict, List, Optional
from src.utils.logger import get_logger

logger = get_logger()


class ActionExecutionResult:
    """Eylem yürütme sonucu veri sınıfı."""

    def __init__(self, success: bool, message: str, action: Optional[Dict[str, Any]] = None):
        self.success = success
        self.message = message
        self.action = action

    def __repr__(self) -> str:
        return f"<ActionExecutionResult success={self.success} message='{self.message}'>"


class ActionRegistry:
    """Eylemleri saklayan, arayan ve çalıştıran sınıf."""

    def __init__(self, actions: Optional[List[Dict[str, Any]]] = None) -> None:
        """ActionRegistry sınıfını başlatır.

        Args:
            actions: Kaydedilecek eylem listesi.
        """
        self._actions: List[Dict[str, Any]] = actions or []
        self._custom_handlers: Dict[str, Callable[..., Any]] = {}

    def set_actions(self, actions: List[Dict[str, Any]]) -> None:
        """Eylem listesini günceller."""
        self._actions = list(actions)

    def register_custom_handler(self, action_type: str, handler: Callable[..., Any]) -> None:
        """Özel eylem türü işleyicisi kaydeder."""
        self._custom_handlers[action_type] = handler

    def filter_actions(self, query: str) -> List[Dict[str, Any]]:
        """Arama metnine veya sayıya göre eylemleri filtreler.

        Args:
            query: Kullanıcının girdiği arama metni veya sayı.

        Returns:
            List[Dict[str, Any]]: Filtrelenmiş ve önceliklendirilmiş eylemler.
        """
        q = str(query).strip().lower()
        if not q:
            return list(self._actions)

        exact_code_matches: List[Dict[str, Any]] = []
        prefix_code_matches: List[Dict[str, Any]] = []
        text_matches: List[Dict[str, Any]] = []

        for action in self._actions:
            code = str(action.get("code", "")).strip().lower()
            title = str(action.get("title", "")).lower()
            desc = str(action.get("description", "")).lower()

            if code == q:
                exact_code_matches.append(action)
            elif code.startswith(q):
                prefix_code_matches.append(action)
            elif q in title or q in desc:
                text_matches.append(action)

        return exact_code_matches + prefix_code_matches + text_matches

    def execute_by_code(self, code: str) -> ActionExecutionResult:
        """Koda göre eşleşen ilk eylemi çalıştırır.

        Args:
            code: Sayı kodu.

        Returns:
            ActionExecutionResult: Yürütme sonucu.
        """
        matches = self.filter_actions(code)
        if not matches:
            msg = f"Kod ile eşleşen eylem bulunamadı: '{code}'"
            logger.warning(msg)
            return ActionExecutionResult(success=False, message=msg)

        target_action = matches[0]
        return self.execute_action(target_action)

    def execute_action(self, action: Dict[str, Any]) -> ActionExecutionResult:
        """Belirtilen eylem nesnesini çalıştırır.

        Args:
            action: Çalıştırılacak eylem sözlüğü.

        Returns:
            ActionExecutionResult: Yürütme sonucu.
        """
        action_type = str(action.get("type", "cmd")).lower()
        command = str(action.get("command", "")).strip()
        title = action.get("title", "Bilinmeyen Eylem")

        logger.info("Eylem çalıştırılıyor: [%s] %s (Tür: %s)", action.get("code"), title, action_type)

        try:
            if action_type in self._custom_handlers:
                result = self._custom_handlers[action_type](action)
                return ActionExecutionResult(
                    success=True,
                    message=f"Özel işleyici tamamlandı: {result}",
                    action=action
                )

            if action_type == "url":
                webbrowser.open(command)
                return ActionExecutionResult(
                    success=True,
                    message=f"URL tarayıcıda açıldı: {command}",
                    action=action
                )

            if action_type == "cmd":
                # Arka planda engellemeden çalıştır (asynchronous execution)
                subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return ActionExecutionResult(
                    success=True,
                    message=f"Komut başlatıldı: {command}",
                    action=action
                )

            msg = f"Desteklenmeyen eylem türü: {action_type}"
            logger.error(msg)
            return ActionExecutionResult(success=False, message=msg, action=action)

        except Exception as e:
            msg = f"Eylem çalıştırılırken hata: {e}"
            logger.error(msg)
            return ActionExecutionResult(success=False, message=msg, action=action)
