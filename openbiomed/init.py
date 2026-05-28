#!/usr/bin/env python3
"""
OpenBioMed 初始化脚本
在 Open WebUI 启动时自动导入预置 skills
"""

import os
import sys
import shutil
import asyncio
from pathlib import Path

# 添加 backend 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

import yaml
from open_webui.models.skills import Skills, SkillForm, SkillMeta
from open_webui.models.models import Models, ModelForm, ModelMeta, ModelParams
from open_webui.models.access_grants import AccessGrants


def parse_frontmatter(content: str):
    """解析 markdown 文件的 frontmatter"""
    if not content.startswith('---'):
        return {}, content

    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content

    frontmatter_text = parts[1].strip()
    body = parts[2].strip()

    try:
        metadata = yaml.safe_load(frontmatter_text) or {}
    except Exception:
        metadata = {}

    return metadata, body


def apply_branding():
    """用 OpenBioMed 品牌资源覆盖默认文件"""
    assets_dir = Path(__file__).parent / 'assets'
    if not assets_dir.exists():
        print("Assets directory not found, skipping branding")
        return

    from open_webui.config import STATIC_DIR, FRONTEND_BUILD_DIR

    # 需要覆盖的 favicon 目标文件，都使用 favicon.png 作为源
    favicon_targets = [
        'favicon.png',
        'favicon-96x96.png',
        'favicon.svg',
        'favicon.ico',
        'favicon-dark.png',
        'apple-touch-icon.png',
    ]

    favicon_src = assets_dir / 'favicon.png'
    logo_src = assets_dir / 'logo.png'

    # 需要覆盖的目录: backend STATIC_DIR + 前端构建输出
    target_dirs = [STATIC_DIR, FRONTEND_BUILD_DIR / 'static', FRONTEND_BUILD_DIR]

    for target_dir in target_dirs:
        if not target_dir.exists():
            continue
        for fname in favicon_targets:
            dst = target_dir / fname
            if favicon_src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(favicon_src, dst)
        # logo/splash 文件用 logo.png，只覆盖 STATIC_DIR
        if target_dir == STATIC_DIR:
            for splash_name in ['logo.png', 'splash.png', 'splash-dark.png']:
                dst = target_dir / splash_name
                if logo_src.exists():
                    shutil.copy2(logo_src, dst)
                    print(f"Branding: {logo_src.name} -> {dst}")


def ensure_signup_enabled():
    """确保 signup 保持开启（兜底防自动关闭）"""
    from open_webui.config import AppConfig
    import sqlite3, json

    db_path = Path(os.environ.get('DATA_DIR', '/app/data')) / 'webui.db'
    if not db_path.exists():
        print("Database not found, skipping signup enforcement")
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute('SELECT data FROM config WHERE id=1')
    row = cursor.fetchone()
    if row:
        data = json.loads(row[0])
        if data.get('ui', {}).get('enable_signup') is not True:
            data.setdefault('ui', {})['enable_signup'] = True
            cursor.execute('UPDATE config SET data=? WHERE id=1', (json.dumps(data),))
            conn.commit()
            print("Signup: forced enable_signup=True in database")
    conn.close()


async def init_default_model():
    """注册默认模型并设置公共访问权限和 System Prompt"""
    model_id = os.environ.get('DEFAULT_MODELS', 'deepseek-v4-pro')

    SYSTEM_PROMPT = """你是 OpenBioMed，一个专业的生物医药智能体。你的职责是协助研究人员和从业人员完成以下工作：

- 蛋白质结构设计、功能预测与突变分析
- 药物分子设计与性质评估
- 生物信息学数据分析与文献挖掘
- 实验方案设计建议与结果解读

请基于科学证据回答，不确定时如实说明。回答应专业、准确、简洁。"""

    existing = await Models.get_model_by_id(model_id)
    if existing:
        print(f"Default model '{model_id}' already registered")

        needs_update = False
        update_meta = existing.meta.model_dump() if existing.meta else {}

        # 补充 capabilities
        if not update_meta.get('capabilities', {}).get('web_search'):
            update_meta.setdefault('capabilities', {})['web_search'] = True
            needs_update = True

        # 补充 description
        if not update_meta.get('description'):
            update_meta['description'] = 'OpenBioMed 生物医药智能体'
            needs_update = True

        # 补充 system prompt
        needs_system = not existing.params or not getattr(existing.params, 'system', None)

        if needs_update or needs_system:
            params_data = existing.params.model_dump() if existing.params else {}
            if needs_system:
                params_data['system'] = SYSTEM_PROMPT
            await Models.update_model_by_id(
                model_id,
                ModelForm(
                    id=model_id,
                    name=model_id,
                    meta=ModelMeta(**update_meta),
                    params=ModelParams(**params_data),
                ),
            )
            print(f"Updated model '{model_id}': {'meta' if needs_update else ''}{' + system prompt' if needs_system else ''}")
        await AccessGrants.set_access_grants('model', model_id, [
            {"principal_type": "user", "principal_id": "*", "permission": "read"}
        ])
        print(f"Ensured public read access for '{model_id}'")
        return

    form_data = ModelForm(
        id=model_id,
        name=model_id,
        meta=ModelMeta(
            description="OpenBioMed 生物医药智能体",
            capabilities={"web_search": True},
        ),
        params=ModelParams(system=SYSTEM_PROMPT),
        access_grants=[
            {"principal_type": "user", "principal_id": "*", "permission": "read"}
        ],
        is_active=True,
    )

    await Models.insert_new_model(form_data, user_id='system')
    print(f"Registered default model '{model_id}' with system prompt and public access")


async def init_skills():
    """初始化预置 skills"""
    skills_dir = Path(__file__).parent / 'skills'

    if not skills_dir.exists():
        print(f"Skills directory not found: {skills_dir}")
        return

    # 查找所有 SKILL.md 文件
    skill_files = list(skills_dir.glob('*/SKILL.md'))

    if not skill_files:
        print("No skills found to import")
        return

    print(f"Found {len(skill_files)} skills to import")

    for skill_file in skill_files:
        try:
            content = skill_file.read_text()
            metadata, body = parse_frontmatter(content)

            skill_id = metadata.get('name', skill_file.parent.name)
            skill_name = metadata.get('name', skill_file.parent.name)
            skill_description = metadata.get('description', '')
            tags = metadata.get('tags', [])

            # 构建完整的 skill content（包含 frontmatter）
            full_content = content

            # 创建 skill form
            form_data = SkillForm(
                id=skill_id,
                name=skill_name,
                description=skill_description,
                content=full_content,
                meta=SkillMeta(tags=tags if isinstance(tags, list) else []),
                is_active=True,
                access_grants=[
                    {"principal_type": "user", "principal_id": "*", "permission": "read"}
                ]
            )

            # 检查 skill 是否已存在
            existing = await Skills.get_skill_by_id(skill_id)
            if existing:
                print(f"Skill '{skill_id}' already exists, updating...")
                await Skills.update_skill_by_id(skill_id, {
                    'name': skill_name,
                    'description': skill_description,
                    'content': full_content,
                    'meta': form_data.meta.model_dump()
                })
            else:
                print(f"Creating skill '{skill_id}'...")
                await Skills.insert_new_skill(
                    user_id='system',  # 使用 system 用户
                    form_data=form_data
                )

            # 确保公共访问权限
            await AccessGrants.set_access_grants('skill', skill_id, [
                {"principal_type": "user", "principal_id": "*", "permission": "read"}
            ])

        except Exception as e:
            print(f"Error importing skill {skill_file}: {e}")
            continue

    print("Skills initialization complete")


async def main():
    """主入口"""
    print("OpenBioMed initialization script starting...")
    apply_branding()
    ensure_signup_enabled()
    await init_default_model()
    await init_skills()
    print("OpenBioMed initialization complete")


if __name__ == '__main__':
    asyncio.run(main())
