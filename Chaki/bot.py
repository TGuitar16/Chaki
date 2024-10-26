# Imports
import discord
from discord.ext import commands
import asyncio
from tokens import CTOKEN

# SetUp
TOKEN = CTOKEN

intents = discord.Intents.all()
intents.message_content = True
intents.members = True

class MyBot(commands.Bot):
  def __init__(self, **kwargs):
    super().__init__(command_prefix='!', intents=intents, **kwargs, help_command=None)
    self.synced = False

  async def on_ready(self):
    print(f'봇이 로그인되었습니다: {self.user.name}')
    if not self.synced:
        await self.tree.sync()
        print("슬래시 명령어가 동기화되었습니다.")
        self.synced = True
        
    commands_list = await self.tree.get_commands() 
    print("현재 등록된 슬래시 명령어:", [command.name for command in commands_list])

    print("봇이 준비되었습니다. 커맨드를 사용할 수 있습니다.")

  async def setup_hook(self):
    print("setup_hook 시작")
    await self.load_extension("commands.etc_commands")  
    await self.load_extension("commands.appointment_commands")  
    await self.load_extension("commands.word_chain_game")
    await self.load_extension("commands.list_commands") 
    await self.load_extension("commands.gambling_commands")
    print("모든 명령어가 로드되었습니다.")

bot = MyBot()

# Run
async def main():
  async with bot:
    await bot.start(TOKEN)

if __name__ == "__main__":
  asyncio.run(main())

# ver 1.1.0