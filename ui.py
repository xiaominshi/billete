import tkinter as tk
from tkinter import scrolledtext, messagebox
from logic import Logic

class BilleteApp:
    def __init__(self, root):
        self.logic = Logic()
        self.root = root
        self.root.title("LULI专属 (Python Version)")
        self.root.geometry("500x700")
        self.root.resizable(False, False)

        # Input Area (Entrada)
        self.input_label = tk.Label(root, text="请输入代码 (Input Code):")
        self.input_label.pack(pady=(10, 0))
        
        self.input_text = scrolledtext.ScrolledText(root, width=55, height=10)
        self.input_text.pack(pady=5)

        # Middle Controls Panel
        self.controls_frame = tk.Frame(root)
        self.controls_frame.pack(pady=5, padx=10, fill="x")

        # Row 1: Luggage
        self.luggage_frame = tk.Frame(self.controls_frame)
        self.luggage_frame.pack(fill="x", pady=2)

        tk.Label(self.luggage_frame, text="手提行李:").pack(side="left")
        self.hand_entry = tk.Entry(self.luggage_frame, width=3)
        self.hand_entry.insert(0, "1")
        self.hand_entry.pack(side="left", padx=2)

        tk.Label(self.luggage_frame, text="件").pack(side="left")
        self.hand_weight_entry = tk.Entry(self.luggage_frame, width=3)
        self.hand_weight_entry.insert(0, "8")
        self.hand_weight_entry.pack(side="left", padx=2)
        tk.Label(self.luggage_frame, text="kg").pack(side="left", padx=(0, 10))

        tk.Label(self.luggage_frame, text="托运行李:").pack(side="left")
        self.pack_entry = tk.Entry(self.luggage_frame, width=3)
        self.pack_entry.insert(0, "2")
        self.pack_entry.pack(side="left", padx=2)
        
        tk.Label(self.luggage_frame, text="件").pack(side="left")
        self.pack_weight_entry = tk.Entry(self.luggage_frame, width=3)
        self.pack_weight_entry.insert(0, "23")
        self.pack_weight_entry.pack(side="left", padx=2)
        tk.Label(self.luggage_frame, text="kg").pack(side="left")

        # Row 2: Passenger Info
        self.passenger_frame = tk.Frame(self.controls_frame)
        self.passenger_frame.pack(fill="x", pady=5)

        tk.Label(self.passenger_frame, text="护照号码:").pack(side="left")
        self.passport_entry = tk.Entry(self.passenger_frame, width=15, state="disabled")
        self.passport_entry.pack(side="left", padx=5)

        tk.Label(self.passenger_frame, text="旅客姓名:").pack(side="left")
        self.name_entry = tk.Entry(self.passenger_frame, width=15, state="disabled")
        self.name_entry.pack(side="left", padx=5)

        # Row 3: Checkbox and Buttons
        self.action_frame = tk.Frame(self.controls_frame)
        self.action_frame.pack(fill="x", pady=5)

        self.pdf_var = tk.BooleanVar()
        self.pdf_check = tk.Checkbutton(self.action_frame, text="PDF生成", variable=self.pdf_var, command=self.toggle_pdf_fields)
        self.pdf_check.pack(side="left")

        self.top_var = tk.BooleanVar(value=True)
        self.top_check = tk.Checkbutton(self.action_frame, text="Top", variable=self.top_var, command=self.toggle_top)
        self.top_check.pack(side="left", padx=10)

        # Buttons
        self.btn_frame = tk.Frame(root)
        self.btn_frame.pack(pady=5)

        self.process_btn = tk.Button(self.btn_frame, text="点我点我！！！！", command=self.process_data, bg="#dddddd", width=20)
        self.process_btn.pack(pady=2)

        self.pdf_btn = tk.Button(self.btn_frame, text="生成PDF/Word", command=self.generate_docs, state="disabled", width=20)
        self.pdf_btn.pack(pady=2)

        # Output Area (Salida)
        tk.Label(root, text="输出结果 (Output):").pack(pady=(10, 0))
        self.output_text = scrolledtext.ScrolledText(root, width=55, height=10)
        self.output_text.pack(pady=5)
        
        # Initial Topmost setting
        self.root.attributes('-topmost', True)

    def toggle_pdf_fields(self):
        state = "normal" if self.pdf_var.get() else "disabled"
        self.passport_entry.config(state=state)
        self.name_entry.config(state=state)
        self.pdf_btn.config(state=state)

    def toggle_top(self):
        self.root.attributes('-topmost', self.top_var.get())

    def process_data(self):
        code = self.input_text.get("1.0", tk.END).strip()
        if not code:
            messagebox.showwarning("Warning", "请输入代码！！")
            return
        
        try:
            # Parse logic
            result_text = self.logic.process(code)
            
            # Append Luggage Info
            pack_count = self.pack_entry.get()
            pack_weight = self.pack_weight_entry.get()
            hand_count = self.hand_entry.get()
            hand_weight = self.hand_weight_entry.get()
            
            luggage_info = f"\n经济舱往返 欧\n托运行李{pack_count} 件,每件{pack_weight}公斤\n手提行李{hand_count}件{hand_weight} 公斤\n"
            final_result = result_text + luggage_info
            
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, final_result)
            
            # Update Passenger Info fields for PDF if found
            if self.logic.passengers:
                p = self.logic.passengers[0]
                self.name_entry.config(state="normal")
                self.name_entry.delete(0, tk.END)
                self.name_entry.insert(0, p['name'])
                
                self.passport_entry.config(state="normal")
                self.passport_entry.delete(0, tk.END)
                self.passport_entry.insert(0, p['passport'])
                
                # Re-disable if checkbox not checked? 
                # Keep normal for now as we populated it.
            
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(final_result)
            messagebox.showinfo("Success", "结果已经成功复制到粘贴板！")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def generate_docs(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Warning", "请输入旅客名字！！")
            return
        
        messagebox.showinfo("Info", f"Generating docs for {name}...\n(Feature coming soon)")

def run_gui():
    root = tk.Tk()
    app = BilleteApp(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui()
