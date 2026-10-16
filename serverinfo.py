import os
import app
import localeInfo
import debugInfo

CHINA_PORT = 50000

def BuildServerList(orderList):
	retMarkAddrDict = {}
	retAuthAddrDict = {}
	retRegion0 = {}

	ridx = 1
	for region, auth, mark, channels in orderList:
		cidx = 1
		channelDict = {}
		for channel in channels:
			key = ridx * 10 + cidx
			channel["key"] = key
			channelDict[cidx] = channel
			cidx += 1

		region["channel"] = channelDict

		retRegion0[ridx] = region
		retAuthAddrDict[ridx] = auth
		retMarkAddrDict[ridx*10] = mark
		ridx += 1

	return retRegion0, retAuthAddrDict, retMarkAddrDict

app.ServerName = None

if app.ENABLE_SERVER_SELECT_RENEWAL:
	STATE_NONE = "OFF"
	STATE_DICT = {
		#0 : localeInfo.CHANNEL_STATUS_OFFLINE,
		#1 : localeInfo.CHANNEL_STATUS_VACANT,
		#2 : localeInfo.CHANNEL_STATUS_RECOMMENDED,
		#3 : localeInfo.CHANNEL_STATUS_BUSY,
		#4 : localeInfo.CHANNEL_STATUS_FULL,
		0 : "OFF",
		1 : "ON",
		2 : "ON",
		3 : "ON",
		4 : "ON",
	}

	STATE_REVERSE_DICT = {}
	STATE_COLOR_DICT = { "..." : 0xffdadada} # 퍼블리셔에서 channel상태에 ...을 유지하도 있어서 문제가 발생.
	STATE_COLOR_LIST = [ 0xffffffff, 0xffdadada, 0xff00ff00, 0xffffc000, 0xffff0000 ]

	idx = 0
	for key, value in STATE_DICT.items():
		STATE_REVERSE_DICT[value] = key
		STATE_COLOR_DICT[value] = STATE_COLOR_LIST[idx%len(STATE_COLOR_LIST)]
		idx += 1

	SERVER_STATE_DICT = {
		"NONE" : 0,
		"NEW" : 1,
		"SPECIAL" : 2,
		"CLOSE" : 3
	}

if not app.ENABLE_SERVER_SELECT_RENEWAL:
	if app.ENABLE_CHANNEL_LIST:
		STATE_NONE = "Offline"
		STATE_DICT = { 0 : "Offline", 1 : "Available", 2 : "Busy", 3 : "Full" }
		STATE_COLOR_DICT = { "Offline" : 0xffdadada, "Available" : 0xff00ff00, "Busy" : 0xffffff00, "Full" : 0xffff0000}
	else:
		STATE_NONE = "..."

		STATE_DICT = {
			0 : "....",
			1 : "NORM",
			2 : "BUSY",
			3 : "FULL"
		}

SERVER01_CHANNEL_DICT = {
	1 : {
		"key" : 11,
		"name" : "CH-1   ",
		"ip" : "198.244.215.62",
		"tcp_port" : 12101,
		"udp_port" : 12101,
		"state" : STATE_NONE,
		'count' : 0,
	},
	2 : {
		"key" : 12,
		"name" : "CH-2   ",
		"ip" : "198.244.215.62",
		"tcp_port" : 12201,
		"udp_port" : 12201,
		"state" : STATE_NONE,
		'count' : 0,
	},
	3 : {
		"key" : 13,
		"name" : "CH-3   ",
		"ip" : "198.244.215.62",
		"tcp_port" : 12301,
		"udp_port" : 12301,
		"state" : STATE_NONE,
		'count' : 0,
	},
	4 : {
		"key" : 14,
		"name" : "CH-4   ",
		"ip" : "198.244.215.62",
		"tcp_port" : 12401,
		"udp_port" : 12401,
		"state" : STATE_NONE,
		'count' : 0,
	},
	5 : {
		"key" : 15,
		"name" : "CH-5   ",
		"ip" : "198.244.215.62",
		"tcp_port" : 12501,
		"udp_port" : 12501,
		"state" : STATE_NONE,
		'count' : 0,
	},
	6 : {
		"key" : 16,
		"name" : "CH-6 VIP",
		"ip" : "198.244.215.62",
		"tcp_port" : 12601,
		"udp_port" : 12601,
		"state" : STATE_NONE,
		'count' : 0,
	},
	7 : {
		"key" : 17,
		"name" : "CH-7 VIP",
		"ip" : "198.244.215.62",
		"tcp_port" : 12701,
		"udp_port" : 12701,
		"state" : STATE_NONE,
		'count' : 0,
	},
}

SERVER02_CHANNEL_DICT = {
	1 : {
		"key" : 11,
		"name" : "DEV-1   ",
		"ip" : "198.244.215.62",
		"tcp_port" : 12101,
		"udp_port" : 12101,
		"state" : STATE_NONE,
		'count' : 0,
	},
	2 : {
		"key" : 12,
		"name" : "DEV-2   ",
		"ip" : "198.244.215.62",
		"tcp_port" : 12201,
		"udp_port" : 12201,
		"state" : STATE_NONE,
		'count' : 0,
	},
	3 : {
		"key" : 13,
		"name" : "DEV-3   ",
		"ip" : "198.244.215.62",
		"tcp_port" : 12301,
		"udp_port" : 12301,
		"state" : STATE_NONE,
		'count' : 0,
	},
	4 : {
		"key" : 14,
		"name" : "DEV-4   ",
		"ip" : "198.244.215.62",
		"tcp_port" : 12401,
		"udp_port" : 12401,
		"state" : STATE_NONE,
		'count' : 0,
	},
}

SERVER03_CHANNEL_DICT = {
	1 : {
		"key" : 11,
		"name" : "AMD64-1   ",
		"ip" : "198.244.215.62",
		"tcp_port" : 23101,
		"udp_port" : 23101,
		"state" : STATE_NONE,
		'count' : 0,
	},
}

REGION_NAME_DICT = {
	0 : "Europe",
}

REGION_AUTH_SERVER_DICT = {
	0 : {
		1 : {
			"ip" : "198.244.215.62",
			"port" : 11150,
		},
		2 : {
			"ip" : "198.244.215.62",
			"port" : 11150,
		},
		3 : {
			"ip" : "198.244.215.62",
			"port" : 23150,
		},
	}
}

REGION_DICT = {
	0 : {
		1 : {
			"name" : "Test Server",
			"channel" : SERVER01_CHANNEL_DICT,
			"state" : "NEW",
		},
		2 : {
			"name" : "Dev. FreeBSD",
			"channel" : SERVER02_CHANNEL_DICT,
			"state" : "SPECIAL",
		},
		3 : {
			"name" : "AMD64 Canary",
			"channel" : SERVER03_CHANNEL_DICT,
			"state" : "SPECIAL",
		},
	},
}

MARKADDR_DICT = {
	10 : {
		"ip" : "198.244.215.62",
		"tcp_port" : 12101,
		"mark" : "10.tga",
		"symbol_path" : "10",
	},
	20 : {
		"ip" : "198.244.215.62",
		"tcp_port" : 12101,
		"mark" : "10.tga",
		"symbol_path" : "10",
	},
	30 : {
		"ip" : "198.244.215.62",
		"tcp_port" : 23101,
		"mark" : "10.tga",
		"symbol_path" : "10",
	},
}

TESTADDR = {
	"ip" : "localhost",
	"tcp_port" : 50000,
	"udp_port" : 50000,
}
