import cv2
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import colour
from colour.plotting import *
from scipy.signal import find_peaks
from scipy.optimize import curve_fit

class EspectroscopiaApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry('1200x628')
        self.root.title('Software de Espectroscopia')
        self.root.configure(bg='#f0f0f0')
        
        self.img_arr = None
        self.fig = None
        self.canvas = None
        self.toolbar = None
        
        self.criar_interface()
        
   
        
    def criar_interface(self):
        self.main_frame = tk.Frame(self.root, bg='#f0f0f0')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.botoes_frame = tk.Frame(self.main_frame, bg='#f0f0f0')
        self.botoes_frame.pack(pady=10)

        self.botao1 = tk.Button(
        self.botoes_frame,
        text='Espectro RGB',
        command=self.plotar_espectro_rgb,
        )
        self.botao1.grid(row=0, column=0, padx=5)

        self.botao2 = tk.Button(
            self.botoes_frame,
            text='Espectro continuo',
            command=self.plotar_espectro_continuo,
        )
        self.botao2.grid(row=0, column=1, padx=5)

        self.botao3 = tk.Button(
            self.botoes_frame,
            text='Gray Scale',
            command=self.plotar_escala_cinza
        )
        self.botao3.grid(row=0, column=2, padx=5)

        self.botao4 = tk.Button(
            self.botoes_frame,
            text='Extrair Dados',
            command=self.extrair_dados
        )
        self.botao4.grid(row=0, column=3, padx=5)
        
        self.botao5 = tk.Button(
            self.botoes_frame,
            text='CFMS',
            command=self.plot_single_cmfs
        )
        self.botao5.grid(row=0, column=4, padx=5)
            
        self.frame_graph = tk.Frame(self.main_frame, bg='white', highlightbackground="gray", highlightthickness=1)
        self.frame_graph.pack(fill=tk.BOTH, expand=True)
        self.status_frame = ttk.Frame(self.root)

        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        self.status_label = ttk.Label(
            self.status_frame,
            text="",
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.label_imagem = tk.Label(self.main_frame)
        self.label_imagem.pack()

    def plot_single_cmfs(self):
        plot_single_cmfs(
           "CIE 1931 2 Degree Standard Observer",
            y_label="Sensitivity",
            bounding_box=(390, 870, 0, 1.1),
        )
        
    def calibrar_com_mercurio(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Imagens", "*.jpg *.png *.jpeg")]
        )
        if not filename:
            return
    
    def carregar_imagem(self):
        
        filename = filedialog.askopenfilename(
            filetypes=[("Imagens", "*.jpg *.png *.jpeg"), ("Todos arquivos", "*.*")]
        )
        if not filename:
            return
        
        self.img_arr = cv2.imread(filename)
        self.img_arr = cv2.cvtColor(self.img_arr, cv2.COLOR_BGR2RGB)
        self.img_arr = cv2.GaussianBlur(self.img_arr, (5,5), 0)
        
        self.img = Image.fromarray(self.img_arr)
        self.img = self.img.resize((775, 45))
            
        imagetk = ImageTk.PhotoImage(image=self.img)                
        self.label_imagem.config(image=imagetk)
        self.label_imagem.image = imagetk    
            
    def plotar_espectro_rgb(self):
            
        self.carregar_imagem()
        
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        if self.toolbar:
            self.toolbar.destroy()
        
        self.altura, self.largura, _ = self.img_arr.shape
        self.espectro_r = [np.mean(self.img_arr[:, x, 0])/255 for x in range(self.largura)]
        self.espectro_g = [np.mean(self.img_arr[:, x, 1])/255 for x in range(self.largura)]
        self.espectro_b = [np.mean(self.img_arr[:, x, 2])/255 for x in range(self.largura)]
                
        self.fig = plt.Figure(figsize=(9, 4))
        ax = self.fig.add_subplot(111)
                
        ax.plot(self.espectro_r, color = 'red')#, label="Vermelho (R)")
        ax.plot(self.espectro_g, color = 'green')#, label="Verde (G)")
        ax.plot(self.espectro_b, color='blue')#, label="Azul (B)")
            
        ax.set_title("Espectroscopia RGB da Imagem", fontsize=12)
        ax.set_xlabel("Posição Horizontal na Imagem")
        ax.set_ylabel("Intensidade Normalizada")
        ax.legend()
        ax.grid(True)
            
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graph)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.frame_graph)
        self.toolbar.update()
            
    def plotar_espectro_continuo(self):

        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        if self.toolbar:
            self.toolbar.destroy()
        
        try:
            self.altura, self.largura, _ = self.img_arr.shape
            
            cmfs = colour.MSDS_CMFS["CIE 1931 2 Degree Standard Observer"]
            wavelengths = cmfs.wavelengths
            s_r = cmfs.values[:, 0]
            s_g = cmfs.values[:, 1]
            s_b = cmfs.values[:, 2]
            
            self.comprimentos_onda_mapeados = np.linspace(380, 780, self.largura)
    
            self.s_r_interp = np.interp(self.comprimentos_onda_mapeados, wavelengths, s_r)
            self.s_g_interp = np.interp(self.comprimentos_onda_mapeados, wavelengths, s_g)
            self.s_b_interp = np.interp(self.comprimentos_onda_mapeados, wavelengths, s_b)
            
            self.espectro = (self.espectro_r * self.s_r_interp + self.espectro_g * self.s_g_interp + self.espectro_b * self.s_b_interp)

            picos, _ = find_peaks(self.espectro, prominence=0.1, width=5)
            
            self.fig = plt.Figure(figsize=(9, 4), dpi=100)
            ax = self.fig.add_subplot(111)
            ax.plot(self.comprimentos_onda_mapeados, self.espectro, color='darkviolet')
            ax.scatter(self.comprimentos_onda_mapeados[picos], self.espectro[picos], color='black')
            ax.set_xlabel("Comprimento de Onda (nm)")
            ax.set_ylabel("Intensidade Relativa")
            ax.set_title("Espectro Reconstruído")
            ax.set_xlim(380, 780)
            ax.grid(True, alpha=0.3)
            
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graph)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            self.toolbar = NavigationToolbar2Tk(self.canvas, self.frame_graph)
            self.toolbar.update()

        except Exception as e:
            tk.messagebox.showerror("Erro", f"Falha ao gerar espectro contínuo:\n{str(e)}")

    def plotar_escala_cinza(self):

        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        if self.toolbar:
            self.toolbar.destroy()
        
        try:
            
            ls = colour.SDS_LIGHT_SOURCES["Mercury"]
            ls = ls.align(colour.SpectralShape(380,780, ((780.0 - 380.0) / (float(self.largura) - 1.0))))            
            
            img = cv2.cvtColor(self.img_arr, cv2.COLOR_BGR2GRAY)
            img = cv2.medianBlur(img, 3)
            img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)

            self.img2 = Image.fromarray(img)
            self.img2 = self.img2.resize((775, 45))
            
            imagetk = ImageTk.PhotoImage(image=self.img2)                
            self.label_imagem.config(image=imagetk)
            self.label_imagem.image = imagetk    
            
            perfil = np.mean(img, axis=0)
                
            self.fig = plt.Figure(figsize=(9, 4), dpi=100)
            ax = self.fig.add_subplot(111)
            ax.plot(self.comprimentos_onda_mapeados, (perfil / np.max(perfil)), color='gray')
            ax.plot(ls.domain, ls.range, color='red', label = 'Espectro Mercúrio')
            ax.set_xlabel("Comprimento de Onda (nm)")
            ax.set_ylabel("Intensidade Relativa")
            ax.set_title("Espectro Cinza")
            ax.set_xlim(380, 780)
            ax.grid(True, alpha=0.3)
            
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graph)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            self.toolbar = NavigationToolbar2Tk(self.canvas, self.frame_graph)
            self.toolbar.update()
             
        except Exception as e:
            tk.messagebox.showerror("Erro", f"Falha ao gerar espectro cinza:\n{str(e)}")
                    
    def extrair_dados(self):
        self.status_label.config(text="Exportando CSV...")

        self.dados = np.column_stack((self.comprimentos_onda_mapeados, self.espectro))
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if file_path:
            np.savetxt(file_path, self.dados, delimiter=",", fmt="%.4f")
            self.status_label.config(text=f"CSV exportado: {file_path}")            
        
if __name__ == "__main__":
    root = tk.Tk()
    app = EspectroscopiaApp(root)
    root.mainloop()