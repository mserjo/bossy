# backend/app/src/tasks/system/monitoring.py
# -*- coding: utf-8 -*-
"""
Модуль для завдання збору системних метрик.

Визначає `SystemMetricsCollectorTask`, відповідальний за періодичний
збір основних метрик системи, таких як використання CPU, пам'яті,
дискового простору та мережевої активності (концептуально).

Примітка: для роботи цього модуля потрібна бібліотека `psutil`.
Якщо вона не є залежністю проекту, її потрібно додати (наприклад, `pip install psutil`).
"""

import asyncio
import logging
import psutil # Популярна бібліотека для отримання системних метрик
import shutil # Для shutil.disk_usage
from typing import Any, Dict # Додано для типізації run


from app.src.tasks.base import BaseTask
# from app.src.config.settings import settings # Для можливих налаштувань моніторингу

# Налаштування логера для цього модуля
logger = logging.getLogger(__name__)

class SystemMetricsCollectorTask(BaseTask):
    """
    Завдання для збору та логування основних системних метрик.

    Збирає інформацію про:
    - Використання CPU (загальне та по ядрах)
    - Використання оперативної пам'яті (RAM)
    - Використання віртуальної пам'яті (Swap)
    - Використання дискового простору для ключових розділів
    - Мережева активність (загальні лічильники переданих/отриманих байт)

    Зібрані метрики переважно логуються. В реальній системі вони
    могли б відправлятися до системи моніторингу (наприклад, Prometheus, Grafana).
    """

    def __init__(self, name: str = "SystemMetricsCollectorTask"):
        """
        Ініціалізація завдання збору метрик.
        """
        super().__init__(name)
        # Тут можна додати налаштування, наприклад, які диски моніторити
        # self.disk_partitions_to_monitor = settings.MONITORED_DISK_PARTITIONS or ['/']
        self.disk_partitions_to_monitor = ['/'] # Приклад, моніторимо кореневий розділ
        # Перевірка доступності psutil
        if not hasattr(psutil, 'cpu_times_percent'):
            self.logger.error("Бібліотека 'psutil' не завантажена або неповна. Завдання не зможе збирати метрики.")
            # Можна встановити прапорець помилки і не виконувати run, або прокинути виняток
            self.initialization_failed = True
        else:
            self.initialization_failed = False


    async def _get_cpu_usage(self) -> dict:
        """Збирає інформацію про використання CPU."""
        # interval=0.1 може бути досить коротким; для меншого навантаження можна збільшити
        cpu_times = psutil.cpu_times_percent(interval=0.1, percpu=False)
        # percpu=True може бути ресурсомістким на системах з великою кількістю ядер.
        # Розгляньте можливість не збирати percpu дані, якщо вони не критичні.
        cpu_times_per_cpu_list = []
        try:
            cpu_times_per_cpu = psutil.cpu_times_percent(interval=0.1, percpu=True)
            for i, core in enumerate(cpu_times_per_cpu):
                cpu_times_per_cpu_list.append({
                    f"cpu_{i}_user": core.user,
                    f"cpu_{i}_system": core.system,
                    f"cpu_{i}_idle": core.idle,
                })
        except Exception as e:
            self.logger.warning(f"Не вдалося зібрати метрики CPU по ядрах: {e}")


        return {
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "cpu_count_physical": psutil.cpu_count(logical=False),
            "total_usage_user_percent": cpu_times.user,
            "total_usage_system_percent": cpu_times.system,
            "total_usage_idle_percent": cpu_times.idle,
            "per_cpu_usage": cpu_times_per_cpu_list
        }

    async def _get_memory_usage(self) -> dict:
        """Збирає інформацію про використання оперативної та віртуальної пам'яті."""
        virtual_mem = psutil.virtual_memory()
        swap_mem = psutil.swap_memory()
        return {
            "virtual_total_gb": round(virtual_mem.total / (1024**3), 2),
            "virtual_available_gb": round(virtual_mem.available / (1024**3), 2),
            "virtual_used_gb": round(virtual_mem.used / (1024**3), 2),
            "virtual_percent_used": virtual_mem.percent,
            "swap_total_gb": round(swap_mem.total / (1024**3), 2) if swap_mem.total > 0 else 0,
            "swap_used_gb": round(swap_mem.used / (1024**3), 2) if swap_mem.total > 0 else 0,
            "swap_free_gb": round(swap_mem.free / (1024**3), 2) if swap_mem.total > 0 else 0,
            "swap_percent_used": swap_mem.percent if swap_mem.total > 0 else 0,
        }

    async def _get_disk_usage(self) -> dict:
        """Збирає інформацію про використання дискового простору."""
        disk_usage_stats = {}
        for partition_path in self.disk_partitions_to_monitor:
            try:
                # Нормалізація шляху для імені ключа
                # Наприклад, "/" -> "root", "/var/log" -> "var_log"
                key_name = partition_path.replace('/', '_').strip('_')
                if not key_name: # для "/"
                    key_name = "root"

                usage = shutil.disk_usage(partition_path)
                disk_usage_stats[f"disk_{key_name}"] = {
                    "path": partition_path,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percent_used": round((usage.used / usage.total) * 100, 2) if usage.total > 0 else 0,
                }
            except FileNotFoundError:
                self.logger.warning(f"Дисковий розділ '{partition_path}' не знайдено для моніторингу.")
            except Exception as e:
                self.logger.error(f"Помилка отримання інформації про диск '{partition_path}': {e}", exc_info=True)
        return disk_usage_stats

    async def _get_network_io(self) -> dict:
        """
        Збирає інформацію про мережеву активність (загальну).
        psutil.net_io_counters() повертає абсолютні значення з моменту завантаження системи.
        Для отримання швидкості передачі (Rate) потрібно порівнювати значення з попереднім виміром.
        Цей приклад показує лише загальні лічильники.
        """
        net_io = psutil.net_io_counters() # `pernic=False` за замовчуванням для загальних лічильників
        return {
            "bytes_sent_total_mb": round(net_io.bytes_sent / (1024**2), 2),
            "bytes_recv_total_mb": round(net_io.bytes_recv / (1024**2), 2),
            "packets_sent_total": net_io.packets_sent,
            "packets_recv_total": net_io.packets_recv,
            "errors_in_total": net_io.errin,
            "errors_out_total": net_io.errout,
            "drop_in_total": net_io.dropin,
            "drop_out_total": net_io.dropout,
        }

    async def run(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Виконує збір всіх системних метрик.
        """
        if self.initialization_failed:
            self.logger.error(f"Завдання '{self.name}' не може бути виконано через помилку ініціалізації (psutil?).")
            return {"error": "Initialization failed, psutil might be missing or incomplete."}

        self.logger.info(f"Запуск завдання '{self.name}'...")
        metrics: Dict[str, Any] = {}
        start_time = asyncio.get_event_loop().time()

        try:
            # Використовуємо asyncio.gather для паралельного збору метрик, де це доцільно
            # Деякі виклики psutil можуть бути блокуючими або потребувати інтервалу,
            # тому повна паралелізація може бути не завжди ефективною без ретельної оцінки.
            # Тут ми викликаємо їх послідовно з невеликими паузами.

            metrics["cpu_usage"] = await self._get_cpu_usage()
            # Даємо невеликий "простір" між вимірами, щоб уникнути взаємного впливу,
            # особливо якщо інтервали в psutil короткі.
            await asyncio.sleep(0.05)
            metrics["memory_usage"] = await self._get_memory_usage()
            await asyncio.sleep(0.05)
            metrics["disk_usage"] = await self._get_disk_usage()
            await asyncio.sleep(0.05)
            metrics["network_io"] = await self._get_network_io()

            self.logger.info(f"Зібрані системні метрики (перший рівень ключів): {list(metrics.keys())}")
            # Для детального логування можна розгорнути:
            # for key, value in metrics.items():
            #     self.logger.debug(f"Метрика '{key}': {value}")
            # Або відправляти `metrics` у систему моніторингу.

        except Exception as e:
            self.logger.error(f"Критична помилка під час виконання завдання '{self.name}': {e}", exc_info=True)
            metrics["error"] = str(e)
            # Відповідно до BaseTask, помилка буде залогована on_failure, якщо прокинути виняток
            raise
        finally:
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            self.logger.info(
                f"Завдання '{self.name}' завершено за {duration:.4f} секунд."
            )
        return metrics

# # Приклад використання (можна видалити або закоментувати):
# # async def main():
# #     logging.basicConfig(
# #         level=logging.DEBUG, # DEBUG для перегляду детальних метрик
# #         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# #     )
# #     metrics_task = SystemMetricsCollectorTask()
# #     if metrics_task.initialization_failed:
# #         logger.error("Не вдалося ініціалізувати завдання збору метрик. Перевірте наявність psutil.")
# #         return
# #
# #     try:
# #         collected_metrics = await metrics_task.execute()
# #         # logger.info(f"Фінальні зібрані метрики в main: {collected_metrics}")
# #         if "error" in collected_metrics:
# #             logger.error(f"Під час збору метрик сталася помилка: {collected_metrics['error']}")
# #     except Exception as e:
# #         logger.error(f"Помилка при виконанні завдання metrics_task: {e}", exc_info=True)
# #
# #
# # if __name__ == "__main__":
# #     # Для Windows може знадобитися: asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# #     asyncio.run(main())
