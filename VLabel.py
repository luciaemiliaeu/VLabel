import pandas as pd 
import numpy as np 
import copy


# Recebe um caminho csv para uma base agrupada
# "rotulo" representa a string dos rótulos
# "labels" representa os rótulos no formato [(id_atributo, fx_inicial, fx_final,tx_acerto)]
class Rotulador(object):
	def __init__ (self, base):
		self.bd = pd.read_csv(base,sep=',',parse_dates=True)
		self.titulos = self.bd.drop(['Cluster'],axis = 1).columns.values.tolist()
		self.grupos = self.group_separator(self.bd)
		self.faixas_iniciais = self.faixas(self.grupos)
		self.faixas_finais = self.verify_fixas(self.faixas_iniciais)
		self.rotulo = self.rotulo(self.titulos, self.grupos, self.faixas_finais)
		self.labels = self.label( self.grupos, self.faixas_finais)

	def faixas(self, grupos):
		faixas = []
		for i in grupos:
			faixas.append(self.calc_faixa(i))
		return faixas

	# recebe um dataframe de n grupos
	# retorna n dataframes, um para cada grupo, sem o atributo cluster
	def group_separator(self, data):
		grouped = data.groupby(['Cluster'])		
		frames = [] 								           
		for nome, grupo in grouped:
			frames.append( grupo.drop(['Cluster'],axis = 1).get_values() )		
		return frames

	# recebe o dataframe de um grupo
	# retorna uma lista de tuplas representando as faixas dos atributos faixas[atributo][(lim_inf, lim_sup)]
	def calc_faixa(self, group):
		faixas = []
		for i in range(0, group.shape[1]):
			attr = group[:,i]	
			attr.sort()
			faixas.append((attr[0], attr[-1]))	
		return faixas	

	# recebe uma lista das faixas de todos os atributos faixas[grupo][atributo][(lim_inf, lim_sup)]
	# retorna uma lista com as faixas sem interseção new_faixas[grupo][atributo][(lim_inf, lim_sup), taxa livre]
	def verify_fixas(self, faixas):

		new_faixas = []
		for j in faixas: # j = ITERA SOBRE OS GRUPO
			faixasGrupo = []
			for i in range(0,len(j)) : # i = ITERA SOBRE O ATRIBUTO
				faixasY = []
				for n in range(0, len(faixas)): faixasY.append(faixas[n][i])
				faixasY.remove(j[i])
				faixa_livre = self.cal_inter(j[i], faixasY)
				if faixa_livre: txa_Flivre = 100*(faixa_livre[1]-faixa_livre[0])/(j[i][1]-j[i][0])
				else: txa_Flivre = 0
				faixasGrupo.append([faixa_livre,txa_Flivre])	
			new_faixas.append(faixasGrupo)
		return new_faixas	
	
	# recebe uma faixaX e um conjunto de faixasY 
	# retorna os limites da fixaX quem não tem interseção 
	def cal_inter(self, faixaX, faixasY):
		label_ = [(faixaX[0], faixaX[1])]
		
		label = label_.pop()
		for j in faixasY:
			X = self.intersecao(label[0], label[1], j[0], j[1])
			for i in X: 
				if  i[0] == i[1]: return None					
				label_.append(i)
			if not label_ :
				break
			label = label_.pop() 
		return label

	# x-> faixa principal
	def intersecao(self, X1, X2, Y1, Y2):
		inter_size = 0
		label = []
		if any([X1 > Y2, Y1 > X2 ]): # nao tem interseção
			label = [(X1, X2)]
		else:
			if X1 >= Y1 and X2 <= Y2: 
				label = [(0, 0)]
			if X1 >= Y1 and X2 > Y2: 
				label = [(Y2, X2)]
			if X1 < Y1 and X2 <= Y2:
				label = [(X1, Y1)]
			if X1 < Y1 and X2 > Y2:
				label = [(X1, Y1), (Y2, X2)]

		return label

	# recebe uma lista com os nomes dos atributos, uma lista de frames dos grupos, uma lista de faixas
	# retorna uma lista de rotulos dos grupos
	def rotulo(self, titulos, grupos, faixas):
		rotulos = []
		for i in range(0, len(grupos)):
			rotulo = "Cluster "+ str(i)+ "  | #Elementos: " + str(grupos[i].shape[0]) + "\n"
			for j in range(0, grupos[0].shape[1]):
				if faixas[i][j][1] != 0:
					num_erros, taxa_acerto = self.cal_erro(faixas[i][j][0], grupos[i][:,j])
					rotulo += titulos[j] + ": " + str(faixas[i][j][0][0]) + ' ~ '+ str(faixas[i][j][0][1]) 
					rotulo += ' | Faixa (%): ' + str(faixas[i][j][1])
					rotulo += ' | #Erros: ' + str(num_erros) + '| Taxa de acerto: '+ str(taxa_acerto)
					rotulo += '\n'
			rotulos.append(rotulo)
		return rotulos

	def label(self, grupos, faixas):
		labels = []
		for i in range(0,len(grupos)):
			for j in range(0,grupos[0].shape[1]):
				gn = []
				if faixas[i][j][1] != 0:
					num_erros, taxa_acerto = self.cal_erro(faixas[i][j][0], grupos[i][:,j])
					gn.append((j,faixas[i][j][0][0],faixas[i][j][0][1],taxa_acerto))
			labels.append(gn)
		return labels
	
	# recebe a lista do attr analisado e sua faixa de valores
	# retorna o numero de erros e a taxa de acerto 
	def cal_erro(self, faixa, data):
		num_erros = 0
		for i in data:
			if i<faixa[0] or i>faixa[1]:
				num_erros += 1
		taxa_acerto = 100*(len(data)-num_erros)/len(data)
		return num_erros, taxa_acerto	
