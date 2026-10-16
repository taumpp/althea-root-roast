
## returns the best matching name of a matching name list
def GetBestMatchingName(name, nameList):
	if len(nameList) == 0:
		return ""

	bestName = nameList[0]
	bestNameLen = len(bestName)
	for elem in nameList:
		curLen = len(elem)
		if curLen < bestNameLen:
			bestName = elem
			bestNameLen = curLen
		elif curLen == bestNameLen:
			plusPos = bestName.find("+")
			plusPosCur = elem.find("+")
			if plusPos > 0 and plusPosCur == plusPos and curLen > plusPosCur + 1:
				tmpBestName = bestName[:plusPos+1] + elem[plusPos+1] + bestName[plusPos+2:]
				if tmpBestName == elem:
					bestName = elem
					bestNameLen = curLen

	return bestName
