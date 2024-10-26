# Imports
import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import pytz

# Data
DATA_FILE = 'appointments.json'

# SetUp
def save_appointments(appointments):
  with open(DATA_FILE, 'w') as f:
    json.dump(appointments, f)

def load_appointments():
  if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
      return json.load(f)
  return {}

# Commands
# SetUp
class AppointmentCommands(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.appointments = load_appointments() 
    self.server_appointments = {}
    print("AppointmentCommands가 초기화되었습니다.")

  def get_server_appointments(self, guild_id):
    if str(guild_id) not in self.server_appointments:
      self.server_appointments[str(guild_id)] = {}
    print(f"서버 ID {guild_id}에 대한 약속 목록을 가져왔습니다: {self.server_appointments[str(guild_id)]}")
    return self.server_appointments[str(guild_id)]

  def save_server_appointments(self, guild_id):
    self.server_appointments[str(guild_id)] = self.get_server_appointments(guild_id)
    save_appointments(self.server_appointments)
    print(f"서버 ID {guild_id}의 약속이 저장되었습니다: {self.server_appointments[str(guild_id)]}")
  # AppointmentMake
  @discord.app_commands.command(name="약속", description="새 약속을 등록합니다.")
  async def 약속(self, interaction: discord.Interaction, 약속_이름: str, 년: int, 월: int, 일: int, 시: int = 0, 분: int = 0):
    try:
      now = datetime.now(pytz.timezone('Asia/Seoul'))
      appointment_date = pytz.timezone('Asia/Seoul').localize(datetime(년, 월, 일, 시, 분))

      if appointment_date < now:
        await interaction.response.send_message("과거 날짜에는 약속을 등록할 수 없습니다.")
        return

      appointment_id = f"{약속_이름}_{년}-{월:02d}-{일:02d}"
      guild_id = interaction.guild.id
      appointments = self.get_server_appointments(guild_id)

      if appointment_id in appointments:
        await interaction.response.send_message(f"이미 등록된 약속입니다: {약속_이름} on {년}/{월}/{일}")
        return

      appointments[appointment_id] = {
        "name": 약속_이름,
        "date": f"{년}/{월:02d}/{일:02d}",
        "time": f"{시:02d}:{분:02d}",
        "participants": []
      }
      self.save_server_appointments(guild_id)

      await interaction.response.send_message(f"약속 {약속_이름}이 등록되었습니다!")
      print(f"약속이 등록되었습니다: {appointments[appointment_id]}")

    # MakeButton
      # JoinButton
      participate_button = discord.ui.Button(label="참가하기", style=discord.ButtonStyle.green)

      async def participate_callback(interaction):
        callback = await self.participate_callback(약속_이름, appointment_id, guild_id)
        await callback(interaction)

      participate_button.callback = participate_callback

      # LeaveButton
      leave_button = discord.ui.Button(label="나가기", style=discord.ButtonStyle.red)

      async def leave_callback(interaction):
        callback = await self.leave_callback(약속_이름, appointment_id, guild_id)
        await callback(interaction)

      leave_button.callback = leave_callback
    # ButtonSetting
      view = discord.ui.View()
      view.add_item(participate_button)
      view.add_item(leave_button)

      await interaction.followup.send("참가하시려면 버튼을 클릭하세요:", view=view)

    # Debug
    except Exception as e:
      await interaction.response.send_message(f"오류 발생: {str(e)}")
      print(f"오류 발생: {str(e)}")

  # Join
  async def participate_callback(self, 약속_이름, appointment_id, guild_id):
    async def callback(interaction: discord.Interaction):
      user = interaction.user
      appointments = self.get_server_appointments(guild_id)

      if user.id in appointments[appointment_id]["participants"]:
        await interaction.response.send_message("이미 참가한 약속입니다.")
      else:
        appointments[appointment_id]["participants"].append(user.id)
        self.save_server_appointments(guild_id)
        await interaction.response.send_message(f"{user.mention}님이 {약속_이름}에 참가했습니다!")

    return callback

  # Leave
  async def leave_callback(self, 약속_이름, appointment_id, guild_id):
    async def callback(interaction: discord.Interaction):
      user = interaction.user
      appointments = self.get_server_appointments(guild_id)

      if user.id not in appointments[appointment_id]["participants"]:
        await interaction.response.send_message("참가하지 않은 약속입니다.")
      else:
        appointments[appointment_id]["participants"].remove(user.id)
        if not appointments[appointment_id]["participants"]:
          del appointments[appointment_id]
          await interaction.response.send_message(f"{약속_이름} 약속이 삭제되었습니다.")
        else:
          await interaction.response.send_message(f"{user.mention}님이 {약속_이름}에서 나갔습니다.")

        self.save_server_appointments(guild_id)

    return callback
  # AppointmentList
  @discord.app_commands.command(name="약속목록", description="서버에서 등록된 약속 목록을 확인합니다.")
  async def 약속목록(self, interaction: discord.Interaction):
    guild_id = interaction.guild.id
    appointments = self.get_server_appointments(guild_id)

    if not appointments:
      await interaction.response.send_message("등록된 약속이 없습니다.")
      return

    appointment_list = "\n".join([f"{id}: {data['name']} on {data['date']} at {data['time']}" for id, data in appointments.items()])
    await interaction.response.send_message(f"등록된 약속 목록:\n{appointment_list}")
  # JoinCommand
  @discord.app_commands.command(name="참가하기", description="약속에 참가합니다.")
  async def 참가하기(self, interaction: discord.Interaction, 약속_이름: str):
    appointment_id = 약속_이름
    guild_id = interaction.guild.id
    appointments = self.get_server_appointments(guild_id)

    if appointment_id not in appointments:
      await interaction.response.send_message(f"존재하지 않는 약속입니다: {약속_이름}")
      return

    user = interaction.user
    if user.id in appointments[appointment_id]["participants"]:
      await interaction.response.send_message("이미 참가한 약속입니다.")
    else:
      appointments[appointment_id]["participants"].append(user.id)
      self.save_server_appointments(guild_id)
      await interaction.response.send_message(f"{user.mention}님이 {약속_이름}에 참가했습니다!")
      print(f"{user.mention}이 {약속_이름}에 참가했습니다.")
  # LeaveCommand
  @discord.app_commands.command(name="나가기", description="약속에서 나갑니다.")
  async def 나가기(self, interaction: discord.Interaction, 약속_이름: str):
    appointment_id = 약속_이름
    guild_id = interaction.guild.id
    appointments = self.get_server_appointments(guild_id)

    if appointment_id not in appointments:
      await interaction.response.send_message(f"존재하지 않는 약속입니다: {약속_이름}")
      return

    user = interaction.user
    if user.id not in appointments[appointment_id]["participants"]:
      await interaction.response.send_message("참가하지 않은 약속입니다.")
    else:
      appointments[appointment_id]["participants"].remove(user.id)
      if not appointments[appointment_id]["participants"]:
        del appointments[appointment_id] 
        await interaction.response.send_message(f"{약속_이름} 약속이 삭제되었습니다.")
        print(f"{약속_이름}의 마지막 참가자가 나갔으므로 약속이 삭제되었습니다.")
      else:
        await interaction.response.send_message(f"{user.mention}님이 {약속_이름}에서 나갔습니다.")
        print(f"{user.mention}이 {약속_이름}에서 나갔습니다.")
    
    self.save_server_appointments(guild_id)

async def setup(bot):
  await bot.add_cog(AppointmentCommands(bot))
