import asyncio
import hashlib
import time
from loguru import logger
from pyrogram.enums import ParseMode
from pyrogram.errors import RPCError
from utils import cleaner
from utils.collector import SubCollector
from utils.check import get_telegram_id_from_message as get_id
from utils.check import check_user
from botmodule.init_bot import config, admin

async def getSubInfo(_, message):
    ID = get_id(message)
    arg = cleaner.ArgCleaner().getall(str(message.text))
    call_time = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
    try:
        back_message = await message.reply("正在查询流量信息...")  # 发送提示
        text = str(message.text)
        url = cleaner.geturl(text)
        arglen = len(arg)
        status = False
        if not url:
            if arglen == 1:
                if await check_user(message, admin, isalert=False):
                    # 管理员至高权限
                    status = True
                else:
                    await back_message.edit_text("仅管理员可查")
                    return
                allsubinfo = config.get_sub()
                item = list(allsubinfo.keys())
                for subname in item:
                    subinfo = config.get_sub(subname)
                    if subinfo:
                        sub_message = await message.reply("正在查询" + subname + "流量信息...")
                        subpwd = subinfo.get('password', '')
                        subowner = subinfo.get('owner', '')
                        url = str(subinfo.get('url', ''))
                        subcl = SubCollector(url)
                        subcl.cvt_enable = False
                        subconfig = await subcl.getSubConfig(inmemory=True)
                        pre_cl = cleaner.ClashCleaner(':memory:', subconfig)
                        proxynum = pre_cl.nodesCount()
                        subinfo = await subcl.getSubTraffic()
                    await printSubNameInfo(subname, subinfo, sub_message, call_time, url, proxynum)
                await back_message.edit_text("所有流量信息查询完毕")
                return
            else:
                pwd = arg[2] if len(arg) > 2 else arg[1]
                subinfo = config.get_sub(arg[1])
                if not subinfo:
                    await back_message.edit_text("❌未找到该订阅")
                    return
                subpwd = subinfo.get('password', '')
                subowner = subinfo.get('owner', '')
                if await check_user(message, admin, isalert=False):
                    # 管理员至高权限
                    url = str(subinfo.get('url', ''))
                    status = True
                else:
                    if subowner and subowner == ID:
                        if hashlib.sha256(pwd.encode("utf-8")).hexdigest() == subpwd:
                            url = str(subinfo.get('url', ''))
                            status = True
                        else:
                            await back_message.edit_text("❌密码错误,请检查后重试")
                            return
                    else:
                        await back_message.edit_text("❌身份ID不匹配，您无权查看该订阅流量信息。")
                        return
        subcl = SubCollector(url)
        subcl.cvt_enable = False
        subinfo = await subcl.getSubTraffic()
        subconfig = await subcl.getSubConfig(inmemory=True)
        pre_cl = cleaner.ClashCleaner(':memory:', subconfig)
        proxynum = pre_cl.nodesCount()
        if status:
            await printSubNameInfo(arg[1], subinfo, back_message, call_time, url, proxynum)
        else:
            await printUrlInfo(url, subinfo, back_message, call_time, proxynum)
    except RPCError as r:
        logger.error(str(r))

async def printSubNameInfo(subname, subinfo, back_message, call_time, url, proxynum):
    if subinfo:
        rs = subinfo[3] - subinfo[2]  # 剩余流量
        subinfo_text = f"""
☁️订阅名称：{subname}
🔗订阅链接：{url}
🌐节点数量：{proxynum}
⬆️已用上行：{round(subinfo[0], 3)} GB
⬇️已用下行：{round(subinfo[1], 3)} GB
🚗总共使用：{round(subinfo[2], 3)} GB
⏳剩余流量：{round(rs, 3)} GB
💧总流量：{round(subinfo[3], 3)} GB
⏱️过期时间：{subinfo[4]}
🔍查询时间：{call_time}
                    """
        await back_message.edit_text(subinfo_text)
    else:
        await back_message.edit_text("此订阅无法获取流量信息")

async def printUrlInfo(url, subinfo, back_message, call_time, proxynum):
    if subinfo:
        rs = subinfo[3] - subinfo[2]  # 剩余流量
        subinfo_text = f"""
🔗订阅链接：{url}
🌐节点数量：{proxynum}
⬆️已用上行：{round(subinfo[0], 3)} GB
⬇️已用下行：{round(subinfo[1], 3)} GB
🚗总共使用：{round(subinfo[2], 3)} GB
⏳剩余流量：{round(rs, 3)} GB
💧总流量：{round(subinfo[3], 3)} GB
⏱️过期时间：{subinfo[4]}
🔍查询时间：{call_time}
            """
        await back_message.edit_text(subinfo_text)
    else:
        await back_message.edit_text("此订阅无法获取流量信息")
