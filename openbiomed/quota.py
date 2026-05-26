"""
OpenBioMed 用户每日限额检查
"""

from datetime import datetime
from fastapi import HTTPException, status


async def check_chat_quota(user):
    """
    检查并递增用户每日聊天限额。
    Admin 用户不受限制。
    超限时抛出 HTTPException(429)。
    """
    if user.role == "admin":
        return

    from open_webui.env import USER_DAILY_QUOTA_LIMIT
    from open_webui.models.user_quotas import UserQuotas

    user_id = user.id
    today = datetime.now().strftime("%Y-%m-%d")

    quota = await UserQuotas.get_by_user_id(user_id)

    current_count = 0
    if quota is not None and quota.quota_date == today:
        current_count = quota.request_count

    if current_count >= USER_DAILY_QUOTA_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"今日免费额度已用完（{USER_DAILY_QUOTA_LIMIT}次），请明天再来！",
        )

    await UserQuotas.increment(user_id, today)