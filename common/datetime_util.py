from datetime import datetime, timezone
import re

def parse_end_at(end_at_str):
    """
    end_atをISO8601またはYYYY-MM-DD形式でパースし、datetime（タイムゾーン付き）で返す。
    失敗時はValueErrorを投げる。
    """
    try:
        # まずISO8601完全一致
        try:
            dt = datetime.fromisoformat(end_at_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            pass
        # YYYY-MM-DD形式
        m = re.match(r"^(\\d{4})-(\\d{2})-(\\d{2})$", end_at_str)
        if m:
            dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=timezone.utc)
            return dt
        # その他は失敗
        raise ValueError
    except Exception:
        raise ValueError("end_atはISO8601形式の日付で指定してください 例: 2025-01-01 または 2025-01-01T12:00:00+09:00")
