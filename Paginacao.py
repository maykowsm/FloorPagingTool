import FreeCAD, FreeCADGui, Part, math, os


path_ui = str(os.path.dirname(__file__))+'/PaginacaoPisoGui.ui'


class Paginacao_gui():
	def __init__(self):
		self.form = FreeCADGui.PySideUic.loadUi(path_ui)

		#Define a função do botão ok
		self.form.btn_ok.clicked.connect(self.accept)

	def accept(self):
		try:
			#Pega os parametros do formulário Gui
			self.comprimento = str(self.form.text_comp.text())
			self.largura = str(self.form.text_larg.text())
			self.junta = str(self.form.text_junta.text())
			self.amarra = str(self.form.text_amarra.text())
			self.especura = str(self.form.text_especura.text())
			self.rotacao = str(self.form.text_rotacao.text())
		except:
			print('Erro - Verifique os valores de entrada. ')

		try:
			#Pega a lista de subobjetos
			self.subelementos = list(FreeCADGui.Selection.getSelectionEx()[0].SubElementNames)
			self.objeto = FreeCADGui.Selection.getSelection()[0]
		except:
			print('Erro - Selecione os objetos na seguinte ordem, 1 - Face, 2 - aresta, 3  - aresta (opcional)')


		obj = FreeCAD.ActiveDocument.addObject('Part::FeaturePython','Piso')
		instancia = Piso(obj,self.comprimento, self.largura, self.junta, self.amarra, self.especura, self.rotacao, self.subelementos, self.objeto)
		obj.ViewObject.Proxy = 0


		FreeCAD.ActiveDocument.recompute()





class Piso():
	def __init__(self , obj ,comprimento, largura, junta, amarra, especura, rotacao, subelementos, objeto):
		obj.Proxy = self

		#Criação das propriedades do objeto
		obj.addProperty("App::PropertyLinkSubList","Objetos","Objeto","Face celecionada")

		obj.addProperty("App::PropertyLength","Comprimento","Dimencoes","Comprimento da peça")
		obj.addProperty("App::PropertyLength","Largura","Dimencoes","Largura da peça")
		obj.addProperty("App::PropertyLength","Junta","Dimencoes","Junta de dilatacao entre a peças")
		obj.addProperty("App::PropertyLength","Amarracao","Dimencoes","Comprimento de transpasse entre as peças")
		obj.addProperty("App::PropertyLength","Espessura","Dimencoes","Espeçura das peças")

		obj.addProperty("App::PropertyAngle","Rotacao","Orientacao","Orientação das peças")

		obj.addProperty("App::PropertyLength","desloca_x","Deslocamento","Deslocamento das peças em X").desloca_x = 0
		obj.addProperty("App::PropertyLength","desloca_y","Deslocamento","Deslocamento das peças em Y").desloca_y = 0

		#Passando os parametros para o objeto
		un = FreeCAD.Units.parseQuantity #objeto que converte uma stringa com numeros e letras para unidades do FreeCAD
		obj.Objetos = (objeto, subelementos)
		obj.Comprimento = un(comprimento)
		obj.Largura = un(largura)
		obj.Junta = un(junta)
		obj.Amarracao = un(amarra)
		obj.Espessura = un(especura)
		obj.Rotacao = un(rotacao)

	def get_pointinit(self): #Retorna o ponto de inicio da paginação
		return self.init_point

	def get_orientation(self):
		return self.orientation

	# def __getstate__(self) -> object:
	# 	return None
	
	# def __setstate__(self, state):
	# 	return None

	def execute(self,obj):
		print("espessura:", obj.Espessura)
		'''Função que é executada toda vez que o objeto precisar ser recalulado'''
		
		#Define a qual plano principal a face está paralela ----------------------------
		orientacao = ''
		sentido = 0 #indica o sentido do vetor normal na direção perpendicular a  face
		normal = obj.Objetos[0][0].Shape.getElement(obj.Objetos[0][1][0]).normalAt(0,0)
		limite = 10**(-10) # limite para ser considerado 0
		print('Normal:'+ str(normal))
		if abs(normal[0]) < limite and abs(normal[1]) < limite and normal[2] != 0:
			orientacao = 'xy'
			sentido = normal[2]

		elif abs(normal[0]) < limite and normal[1] != 0 and abs(normal[2]) < limite:
			orientacao = 'xz'
			sentido = normal[1]

		elif normal[0] != 0 and abs(normal[1]) < limite and abs(normal[2]) < limite:
			orientacao = 'yz'
			sentido = normal[0]

		self.orientation = orientacao
		print('Orientação: '+orientacao)
		print('Sentido: '+str(sentido))
		#---------------------------------------------------------------------------------

		#Definindo o ponto de inicio da modelagem
		p0 = FreeCAD.Vector(0,0,0) #ponto inicial da modelagem
		if len(obj.Objetos[0][1]) > 2:#Verifica se foram celeceionado duas arestas
			#Pega o vertice da interceção entre as duas arestas
			aresta1 = obj.Objetos[0][0].Shape.getElement(obj.Objetos[0][1][1])
			aresta2 = obj.Objetos[0][0].Shape.getElement(obj.Objetos[0][1][2])

			for i in aresta1.Vertexes:
				for j in aresta2.Vertexes:
					if i.Point == j.Point:
						p0 = i.Point
						break
		else: #caso tenha sido celecionado somente uma aresta
			#pega o ponto medio da aresta celecionada
			aresta = obj.Objetos[0][0].Shape.getElement(obj.Objetos[0][1][1])
			vertice1 = aresta.Vertexes[0].Point
			vertice2 = aresta.Vertexes[1].Point
			p0 = FreeCAD.Vector((vertice1[0]+vertice2[0])/2, (vertice1[1]+vertice2[1])/2, (vertice1[2]+vertice2[2])/2)

		self.init_point = p0 
		print(p0)

		#---------------------------------------------------------------------------------------

		#Cria o retangulo inicial e o posiciona na origem do sistema de coordenadas
		''' 
		O retangulo inicial é criado sempre no plano XY para facilitar as rotaçoes e os movimentos de translação, após a criação do objeto completo o mesmo
		rotacionado e colocado na posição desejada
		'''

		base_retangle = Part.makePlane(obj.Comprimento, obj.Largura) # Cria o retangulo base

		#Move o ponto de referencia do retangulo base para a origem do sistema de coordenadas em XY
		if len(obj.Objetos[0][1]) <= 2: #Verifica se foram celeceionado somente uma aresta e uma face
			base_retangle.translate(FreeCAD.Vector(0,obj.Largura/2,0))#desloca o objeto metade do comprimento para a esquerda para centralizar a aresta
		
		#rotaciona o retangulo no angulo especificado com eixo de rotação na origem 
		#base_retangle.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), obj.Rotacao)

		#---------------------------------------------------------------------------------------

		#cria o deslocamento da peça (usado para ajustar a paginação na superfície quando não é feito automaticamente)
		base_retangle.translate(FreeCAD.Vector(obj.desloca_x, obj.desloca_y,0))
		#---------------------------------------------------------------------------------------

		#Verifica o tamanho da face do elemento celecionado

		selection_box = obj.Objetos[0][0].Shape.getElement(obj.Objetos[0][1][0]).BoundBox #retorna o tamanho da caixa de celeção da face
		size_face = [0,0] #tamanho da face celecionada
		if orientacao == 'xy':
			size_face[0] = selection_box.XLength
			size_face[1] = selection_box.YLength
		elif orientacao == 'xz':
			size_face[0] = selection_box.XLength
			size_face[1] = selection_box.ZLength
		elif orientacao == 'yz':
			size_face[0] = selection_box.YLength
			size_face[1] = selection_box.ZLength
		
		print("Tamanho da face:", size_face)
		#-----------------------------------------------------------------------------------------
		
		#Distribui os retangulos em uma linha 

		lineRecList = [base_retangle] #lista  de formas retangulares distribuidas em linha reta
		offset_face = 2 #Tamanho do espaçamento da borda da face

		maiordimencao = max([size_face[0], size_face[1]])
		#Gerando a linha de formas retangulares 
		for i in range(1, int((maiordimencao/obj.Comprimento)*offset_face)): #Cria uma lista linear com 2 vezes o tamanho da face
			#copia para a direita
			rec = base_retangle.copy(True)
			rec.translate(FreeCAD.Vector(i*(obj.Comprimento + obj.Junta),0,0))
			lineRecList.append(rec)
			# Part.show(rec)

			#copia para a esquerda
			rec = base_retangle.copy(True)
			rec.translate(FreeCAD.Vector(-i*(obj.Comprimento + obj.Junta),0,0))
			lineRecList.append(rec)
			# Part.show(rec)

		#-----------------------------------------------------------------------------------------

		#Gera a "matriz" de formas retangulares com base na linha de retangulos - coloca os retangulos em um alista linear

		recShapeList = [] #lista de formas retangulares
		offset_face = 2 #tamanho do espaçamento da borda da face
		for i in range(1, int((maiordimencao/obj.Largura)*offset_face)+1): #lista de retangulos distribuidos na face com base na linha de retangulos
			if i%2 == 0: #Em linhas pares
				#Copia a lista linear de retangulos colocando somente o deslocamento em y 
				for j in lineRecList:
					#Copia para a direção +y
					rec = j.copy(True)
					rec.translate(FreeCAD.Vector(0, i * (obj.Largura + obj.Junta), 0))
					recShapeList.append(rec)
					# Part.show(rec)

					#Copia para a direção -y
					rec = j.copy(True)
					rec.translate(FreeCAD.Vector(0, -i * (obj.Largura + obj.Junta), 0))
					recShapeList.append(rec)
					# Part.show(rec)
			else: # em linhas impares
				#Copia a lista linear de retangulos colocando o deslocamento em y e em x
				for j in lineRecList:
					#Copia para a direção +y
					rec = j.copy(True)
					rec.translate(FreeCAD.Vector(obj.Amarracao, i * (obj.Largura + obj.Junta), 0))
					recShapeList.append(rec)
					# Part.show(rec)

					#Copia para a direção -y
					rec = j.copy(True)
					rec.translate(FreeCAD.Vector(obj.Amarracao, -i * (obj.Largura + obj.Junta), 0))
					recShapeList.append(rec)
					# Part.show(rec)

		
		#coloca a lista de retangulos em linha na "matriz" de retangulos
		for i in lineRecList:
			recShapeList.append(i)

		#---------------------------------------------------------------

		#cria a  forma do corte
		cut = '' #forma do corte
		#Cria a forma do corte 
		if orientacao == 'xy':
			cut = obj.Objetos[0][0].Shape.getElement(obj.Objetos[0][1][0]).copy(True).extrude(FreeCAD.Vector(0,0,sentido*2*obj.Espessura))

		elif orientacao == 'xz':
			cut = obj.Objetos[0][0].Shape.getElement(obj.Objetos[0][1][0]).copy(True).extrude(FreeCAD.Vector(0,sentido*2*obj.Espessura,0))

		elif orientacao == 'yz':
			cut = obj.Objetos[0][0].Shape.getElement(obj.Objetos[0][1][0]).copy(True).extrude(FreeCAD.Vector(sentido*2*obj.Espessura,0,0))


		#---------------------------------------------------------------

		#Move a forma do corte para a origem e rotaciona para ficar no plano xy 
		
		print(FreeCAD.Vector(-p0[0], -p0[1], -p0[2]))
		cut.translate(FreeCAD.Vector(-p0[0], -p0[1], -p0[2]))
		if orientacao == 'xy':
			#Não faz nada
			pass
		elif orientacao == 'xz':
			cut.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0),sentido*90)

		elif  orientacao == 'yz':
			#cut.rotate(FreeCAD.Vector(0,0,0),FreeCAD.Vector(0,0,1),-90)
			cut.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,1,0), -sentido*90)
		
		# Part.show(cut)
		#---------------------------------------------------------------
	
		#rotaciona cria a extruxão e corta cada peça e a coloca em um vetor

		recCutlist = [] #vetor dos retangulos cortados
		for rec in recShapeList:
			part = Part.Shape.common(rec.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), obj.Rotacao).extrude(FreeCAD.Vector(0,0, obj.Espessura)), cut )
			recCutlist.append(part)

		#cria o elemento de piso
		tile = Part.makeCompound(recCutlist)
		# Part.show(tile)
		#---------------------------------------------------------------

		#Posiciona o piso no ponto inicial da paginação
		tile.translate(p0)

		#Rotaciona o piso para ficar na posição correta
		if orientacao == 'xy':
			pass
		elif orientacao == 'xz':
			tile.rotate(p0, FreeCAD.Vector(1,0,0),-sentido*90)

		elif  orientacao == 'yz':
			#tile.rotate(p0,FreeCAD.Vector(0,0,1),90)
			tile.rotate(p0, FreeCAD.Vector(0,1,0), sentido*90)

		# Part.show(tile)
		obj.Placement = tile.Placement
		
		
		obj.Shape = tile
		

		
		
janela = Paginacao_gui()
FreeCADGui.Control.showDialog(janela)