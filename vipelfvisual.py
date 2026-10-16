# Client races for the elf-form Buffi and its VIP outfits (server-src vip_elf_appearance.h).
# Each race folder carries its own 28-bone model and native motions, so the shaman
# motion library of races 10/11 is not used here.
import chr
import chrmgr
import skill

RACES = (
	(65012, 'elf_sentinel_6'),
	(65014, 'elf_k03_ivory'),
	(65015, 'elf_starlit'),
	(65017, 'elf_midnight'),
	(65019, 'elf_maid'),
	(65022, 'elf_nightblade'),
)
# skilldesc MotionIndex of support skills 194-198 and their clip names.
SKILL_CLIPS = ((4, 'hosin'), (5, 'boho'), (6, 'gicheon'), (20, 'kwaesok'), (21, 'jeungryeok'))
_registered = False

def Register():
	global _registered
	if _registered:
		return
	for race, folder in RACES:
		chrmgr.CreateRace(race)
		chrmgr.SelectRace(race)
		chrmgr.SetPathName("d:/ymir work/monster/" + folder + "/")
		chrmgr.LoadRaceData(folder + ".msm")
		chrmgr.RegisterMotionMode(chr.MOTION_MODE_GENERAL)
		for index, name in ((chr.MOTION_WAIT, "wait.msa"), (chr.MOTION_WALK, "walk.msa"), (chr.MOTION_RUN, "run.msa"), (chr.MOTION_DEAD, "dead.msa")):
			chrmgr.RegisterMotionData(chr.MOTION_MODE_GENERAL, index, name, 100)
		# Buffi casts support skills 194-198 through the skill motion slots
		# (RecvSupportUseSkill: MOTION_SKILL + index + grade * SKILL_GRADEGAP).
		# Each skill and grade has its own clip: the elf body motion plus the
		# stock shaman cast effects (MotionEventData of <skill>_target/_2/_3/_4).
		# SPECIAL_1/2 stay unregistered on purpose: the elf FUNC_MOB_SKILL move
		# packet would otherwise restart an effect-less clip over the cast;
		# InterceptMotion ignores an unregistered motion.
		for grade in range(4):
			suffix = "" if grade == 0 else "_%d" % (grade + 1)
			for offset, name in SKILL_CLIPS:
				chrmgr.RegisterMotionData(chr.MOTION_MODE_GENERAL, chr.MOTION_SKILL + offset + grade * skill.SKILL_GRADEGAP, "buff_" + name + suffix + ".msa", 100)
	_registered = True
