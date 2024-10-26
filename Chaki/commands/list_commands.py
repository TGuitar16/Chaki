import discord
from discord.ext import commands

class ListCommands(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @discord.app_commands.command(name="목록", description="명령어 목록을 확인합니다.")
  async def 목록(self, interaction: discord.Interaction):
    commands_list = [command.name for command in self.bot.tree.get_commands()]
    response = "등록된 명령어 목록:\n" + "\n".join(commands_list)
    await interaction.response.send_message(response)

async def setup(bot):
  await bot.add_cog(ListCommands(bot))
