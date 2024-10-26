import discord
from discord.ext import commands

class EtcCommands(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @discord.app_commands.command(name="자기소개", description="봇에 대한 설명입니다.")
  async def 자기소개(self, interaction: discord.Interaction):
    await interaction.response.send_message("저는 Chaki에요!\n약속, 끝말잇기 등의 기능을 지원해요.\n/목록을 입력해 사용 가능한 명령어 목록을 확인하세요")

  @discord.app_commands.command(name="나는", description="봇에게 자기 이름을 알려줍니다.")
  async def 나는(self, interaction: discord.Interaction, 이름: str):
    await interaction.response.send_message(f'안녕 {이름}! 나는 Chaki야.')

  @discord.app_commands.command(name="청소", description="채팅을 지웁니다")
  async def 청소(self, interaction: discord.Interaction, num: int):
    if num < 1:
      await interaction.response.send_message("지울 메시지 수는 1 이상이어야 합니다.", ephemeral=True)
      return
    deleted = await interaction.channel.purge(limit=num)
    await interaction.response.send_message(f'{len(deleted)}개의 메시지를 삭제했습니다.', ephemeral=True)

  @discord.app_commands.command(name="청소", description="채팅을 지웁니다")
  async def 청소(self, interaction: discord.Interaction, num: int):
    if num < 1:
      await interaction.response.send_message("지울 메시지 수는 1 이상이어야 합니다.", ephemeral=True)
      return
    
    if num > 100:
      await interaction.response.send_message("100 이하의 수를 입력하세요.", ephemeral=True)
      return
    deleted = await interaction.channel.purge(limit=num)
    await interaction.response.send_message(f'{len(deleted)}개의 메시지를 삭제했습니다.', ephemeral=True)
    
async def setup(bot):
  await bot.add_cog(EtcCommands(bot))