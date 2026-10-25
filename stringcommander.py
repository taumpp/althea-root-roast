import _weakref

class CallBackFunction:
	class __noarg_call__:
		def __init__(self, cls, obj, func):
			self.cls=cls
			self.obj=_weakref.proxy(obj)
			self.func=_weakref.proxy(func)

		def __call__(self, *arg):
			return self.func(self.obj)

	class __arg_call__:
		def __init__(self, cls, obj, func):
			self.cls=cls
			self.obj=_weakref.proxy(obj)
			self.func=_weakref.proxy(func)

		def __call__(self, *arg):
			return self.func(self.obj, *arg)

	def __init__(self, mfunc, variadic=False):
		self.argCount=mfunc.__func__.__code__.co_argcount
		# Opt in per wire command. Existing commands keep their fixed arity and
		# surplus-token truncation; paginated envelopes retain their full payload.
		self.variadic = variadic

		if self.argCount>1 or variadic:
			self.call=CallBackFunction.__arg_call__(mfunc.__self__.__class__, mfunc.__self__, mfunc.__func__)
		else:
			self.call=CallBackFunction.__noarg_call__(mfunc.__self__.__class__, mfunc.__self__, mfunc.__func__)

	def __call__(self, *arg):
		return self.call(*arg)

	def GetArgumentCount(self):
		return self.argCount

class Analyzer:
	def __init__(self):
		self.cmdDict={}

	def SAFE_RegisterCallBack(self, cmd, callBackFunc, variadic=False):
		self.cmdDict[cmd]=CallBackFunction(callBackFunc, variadic)

	def Run(self, line):
		tokens=line.split()

		if len(tokens)==0:
			return 1

		cmd=tokens.pop(0)

		try:
			callBackFunc=self.cmdDict[cmd]
		except KeyError:
			return 0

		argCount=callBackFunc.GetArgumentCount()-1

		if len(tokens)<argCount:
			raise RuntimeError("Analyzer.Run(line=%s) - cmd=%s, curArgCount[%d]<needArgCount[%d]" % (line, cmd, len(tokens), argCount))
			return 0

		if not callBackFunc.variadic:
			tokens=tokens[:argCount]
		callBackFunc(*tokens)
		return 1
