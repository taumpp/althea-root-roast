import wndMgr


class Expr(object):
	def __init__(self, name=None, op=None, left=None, right=None):
		self.name = name
		self.op = op
		self.left = left
		self.right = right

	def __int__(self):
		return int(self.EvaluateLeaf(self.GetScreenSize()))

	# py3: C-level integer conversion (PyArg_ParseTuple "i", PyLong_AsLong)
	# no longer falls back to __int__ (removed in 3.10); mirror it here so
	# Expr objects passed straight into binary bindings still convert.
	def __index__(self):
		return int(self.EvaluateLeaf(self.GetScreenSize()))

	def __float__(self):
		return float(self.EvaluateLeaf(self.GetScreenSize()))

	def __lt__(self, other):
		ctx = self.GetScreenSize()
		return self.EvaluateLeaf(ctx) < self.GetNewNumber(other, ctx)

	def __le__(self, other):
		ctx = self.GetScreenSize()
		return self.EvaluateLeaf(ctx) <= self.GetNewNumber(other, ctx)

	def __gt__(self, other):
		ctx = self.GetScreenSize()
		return self.EvaluateLeaf(ctx) > self.GetNewNumber(other, ctx)

	def __ge__(self, other):
		ctx = self.GetScreenSize()
		return self.EvaluateLeaf(ctx) >= self.GetNewNumber(other, ctx)

	def GetScreenSize(self):
		return {
			"SCREEN_WIDTH": wndMgr.GetScreenWidth(),
			"SCREEN_HEIGHT": wndMgr.GetScreenHeight(),
		}

	def GetNewNumber(self, x, ctx):
		if isinstance(x, Expr):
			return x.EvaluateLeaf(ctx)
		return x

	def EvaluateLeaf(self, ctx):
		if self.name:
			return ctx[self.name]

		if self.op == "int":
			return int(self.GetNewNumber(self.left, ctx))

		if self.op == "float":
			return float(self.GetNewNumber(self.left, ctx))

		l = self.GetNewNumber(self.left, ctx)
		r = self.GetNewNumber(self.right, ctx)

		if self.op == "+":
			return l + r
		if self.op == "-":
			return l - r
		if self.op == "*":
			return l * r
		if self.op == "/":
			return l / r
		if self.op == "//":
			return l // r

		raise ValueError("Unknown op %s" % self.op)

	def __add__(self, other):
		return Expr(op="+", left=self, right=other)

	def __sub__(self, other):
		return Expr(op="-", left=self, right=other)

	def __mul__(self, other):
		return Expr(op="*", left=self, right=other)

	def __truediv__(self, other):
		return Expr(op="/", left=self, right=other)

	def __floordiv__(self, other):
		return Expr(op="//", left=self, right=other)

	def __radd__(self, other):
		return Expr(op="+", left=other, right=self)

	def __rsub__(self, other):
		return Expr(op="-", left=other, right=self)

	def __rmul__(self, other):
		return Expr(op="*", left=other, right=self)

	def __rtruediv__(self, other):
		return Expr(op="/", left=other, right=self)

	def __rfloordiv__(self, other):
		return Expr(op="//", left=other, right=self)
