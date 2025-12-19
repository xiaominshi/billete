
import java.awt.Component;
import java.awt.ComponentOrientation;
import java.awt.EventQueue;
import java.awt.Font;
import java.awt.LayoutManager;
import java.awt.Toolkit;
import java.awt.datatransfer.ClipboardOwner;
import java.awt.datatransfer.StringSelection;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.KeyAdapter;
import java.awt.event.KeyEvent;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Scanner;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.UIManager;
import javax.swing.UnsupportedLookAndFeelException;

import org.apache.poi.xwpf.usermodel.ParagraphAlignment;
import org.apache.poi.xwpf.usermodel.XWPFDocument;
import org.apache.poi.xwpf.usermodel.XWPFParagraph;
import org.apache.poi.xwpf.usermodel.XWPFRun;
import org.apache.poi.xwpf.usermodel.XWPFTable;
import org.apache.poi.xwpf.usermodel.XWPFTableRow;
import com.itextpdf.text.DocumentException;
import java.awt.BorderLayout;
import javax.swing.JCheckBox;
import javax.swing.ImageIcon;
import java.awt.Color;
import javax.swing.JScrollPane;

/* renamed from: Fly */
public class Billete {
	/* access modifiers changed from: private */
	public JTextArea entrada;
	/* access modifiers changed from: private */
	public JFrame frame;
	private HashMap<String, String> map;
	private ArrayList<Pasajeros> pasajerosLs;
	private ArrayList<VueloInformacion> vuelosLs;
	private ArrayList<EscalaTime> tiempoLs;
	private ArrayList<EscalaTime> pasaporte;
	private ArrayList<EscalaTime> num_billete;
	private JTextField pack;
	private JTextField peso;
	private JTextField hand;
	private JTextField hand_peso;
	private JTextField pasaporte_1;
	private JButton btnpdf;
	private JTextField name;
	private JTextArea salida;
	private JCheckBox chckbxNewCheckBox;
	private JCheckBox chckbxTop_1;
	private JScrollPane scrollPane;
	private JScrollPane scrollPane_salida;
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			public void run() {
				try {
					new Billete().frame.setVisible(true);
				} catch (Exception e) {
					e.printStackTrace();
				}
			}
		});
	}

	public Billete() {
		initialize();
	}

	private void initialize() {
		try {
			for (javax.swing.UIManager.LookAndFeelInfo info : javax.swing.UIManager.getInstalledLookAndFeels()) {
				if ("Nimbus".equals(info.getName())) {
					javax.swing.UIManager.setLookAndFeel(info.getClassName());
					break;
				}
			}
		} catch (Exception e) {
			System.out.println(e);
		}

		this.pasajerosLs = new ArrayList<>();
		this.vuelosLs = new ArrayList<>();
		this.tiempoLs = new ArrayList<>();
		this.pasaporte = new ArrayList<>();
		this.num_billete = new ArrayList<>();
		this.map = new HashMap<>();
		getFly();
		this.frame = new JFrame();
		frame.setAlwaysOnTop(true);
		frame.setResizable(false);
		frame.setFont(new Font("Arial Black", Font.PLAIN, 12));
		frame.setForeground(Color.RED);
		frame.setIconImage(Toolkit.getDefaultToolkit().getImage(Billete.class.getResource("/images/lovee.png")));
		frame.setTitle("季露露专属");
		this.frame.setBounds(100, 100, 483, 649);
		this.frame.setDefaultCloseOperation(3);
		this.frame.getContentPane().setLayout((LayoutManager) null);
		frame.getContentPane().setLayout(null);
		frame.getContentPane().setLayout(null);
		frame.getContentPane().setLayout(null);
		frame.getContentPane().setLayout(null);
		frame.getContentPane().setLayout(null);
		frame.getContentPane().setLayout(null);
		frame.getContentPane().setLayout(null);
		frame.getContentPane().setLayout(null);
		this.entrada = new JTextArea();
//		entrada.setBounds(0, 21, 468, 234);
		this.entrada.addKeyListener(new KeyAdapter() {
			@Override
			public void keyPressed(KeyEvent e) {

				if (e.getKeyCode() == KeyEvent.VK_TAB) {

					if (e.getModifiersEx() > 0) {

						entrada.transferFocusBackward();

					} else {
						entrada.transferFocus();
					}

					e.consume();

				}
			}

		});
		frame.getContentPane().setLayout(null);
		frame.getContentPane().setLayout(null);
		frame.getContentPane().setLayout(null);
		frame.getContentPane().setLayout(null);
		frame.getContentPane().setLayout(null);
		frame.getContentPane().setLayout(null);
		frame.getContentPane().setLayout(null);

//		this.frame.getContentPane().add(this.entrada);
//		this.entrada.setColumns(10);
		
		this.entrada = new JTextArea();
		this.scrollPane = new JScrollPane(entrada); // 创建一个包含JTextArea的滚动面板
		this.scrollPane.setBounds(0, 21, 468, 234); // 设置滚动面板的大小和位置
		frame.getContentPane().add(scrollPane); // 将滚动面板添加到frame中

		salida = new JTextArea();
//		salida.setBounds(0, 354, 468, 257);
		salida.setTabSize(5);
		salida.setEditable(false);
//		this.frame.getContentPane().add(salida);
//		salida.setColumns(5);
		this.scrollPane_salida = new JScrollPane(salida); // 创建一个包含JTextArea的滚动面板
		this.scrollPane_salida.setBounds(0, 354, 468, 257); // 设置滚动面板的大小和位置
		frame.getContentPane().add(scrollPane_salida); // 将滚动面板添加到frame中

		hand = new JTextField();
		hand.setBounds(62, 258, 27, 24);
		hand.addKeyListener(new KeyAdapter() {
			@Override
			public void keyPressed(KeyEvent e) {

				if (e.getKeyCode() == KeyEvent.VK_TAB) {

					if (e.getModifiersEx() > 0) {

						hand.transferFocusBackward();

					} else {
						hand.transferFocus();
					}

					e.consume();

				}
			}

		});
		this.frame.getContentPane().add(hand);
		hand.setColumns(1);
		hand.setText("1");

		pack = new JTextField();
		pack.setBounds(227, 258, 27, 24);
		pack.setColumns(1);
		pack.addKeyListener(new KeyAdapter() {
			@Override
			public void keyPressed(KeyEvent e) {

				if (e.getKeyCode() == KeyEvent.VK_TAB) {

					if (e.getModifiersEx() > 0) {

						pack.transferFocusBackward();

					} else {
						pack.transferFocus();
					}

					e.consume();

				}
			}

		});
		frame.getContentPane().add(pack);
		pack.setText("2");

		JLabel handbag = new JLabel("手提行李:");
		handbag.setBounds(10, 258, 56, 24);
		frame.getContentPane().add(handbag);

		JLabel baggage = new JLabel("托运行李:");
		baggage.setBounds(173, 259, 64, 22);
		frame.getContentPane().add(baggage);

		JLabel baggage_peso = new JLabel("托运行李重量:");
		baggage_peso.setBounds(264, 259, 88, 22);
		frame.getContentPane().add(baggage_peso);

		peso = new JTextField();
		peso.setBounds(341, 258, 27, 24);
		peso.setText("23");
		peso.setColumns(1);
		peso.addKeyListener(new KeyAdapter() {
			@Override
			public void keyPressed(KeyEvent e) {

				if (e.getKeyCode() == KeyEvent.VK_TAB) {

					if (e.getModifiersEx() > 0) {

						peso.transferFocusBackward();

					} else {
						peso.transferFocus();
					}

					e.consume();

				}
			}

		});
		frame.getContentPane().add(peso);

		JLabel Code = new JLabel("Introducir el código");
		Code.setBounds(0, 0, 468, 24);
		Code.setFont(new Font("Tahoma", Font.PLAIN, 13));
		Code.setHorizontalAlignment(0);
		this.frame.getContentPane().add(Code);
		final JButton get = new JButton("点我点我！！！！");
		get.setBounds(0, 318, 236, 35);
		get.setIcon(new ImageIcon(Billete.class.getResource("/images/click.png")));
		get.setFont(new Font("SimSun", 1, 11));
		get.addKeyListener(new KeyAdapter() {
			@Override
			public void keyPressed(KeyEvent e) {

				if (e.getKeyCode() == KeyEvent.VK_TAB) {

					if (e.getModifiersEx() > 0) {

						get.transferFocusBackward();

					} else {
						get.transferFocus();
					}
					e.consume();

				}
				if (e.getKeyCode() == KeyEvent.VK_ENTER) {

					getAndcopy();
					e.consume();

				}
			}

		});
		get.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				getAndcopy();

			}
		});
		this.frame.getContentPane().add(get);

		JLabel handbag_1 = new JLabel("公斤:");
		handbag_1.setBounds(99, 259, 36, 22);
		frame.getContentPane().add(handbag_1);

		hand_peso = new JTextField();
		hand_peso.setBounds(131, 258, 27, 24);
		hand_peso.setText("8");
		hand_peso.setColumns(1);
		hand_peso.addKeyListener(new KeyAdapter() {
			@Override
			public void keyPressed(KeyEvent e) {

				if (e.getKeyCode() == KeyEvent.VK_TAB) {

					if (e.getModifiersEx() > 0) {

						hand_peso.transferFocusBackward();

					} else {
						hand_peso.transferFocus();
					}

					e.consume();

				}
			}

		});
		frame.getContentPane().add(hand_peso);

		JLabel pasaporte = new JLabel("护照号码:");
		pasaporte.setBounds(10, 285, 64, 22);
		frame.getContentPane().add(pasaporte);

		pasaporte_1 = new JTextField();
		pasaporte_1.setBounds(62, 284, 99, 24);
		pasaporte_1.setEnabled(false);
		pasaporte_1.setColumns(1);
		pasaporte_1.addKeyListener(new KeyAdapter() {
			@Override
			public void keyPressed(KeyEvent e) {

				if (e.getKeyCode() == KeyEvent.VK_TAB) {

					if (e.getModifiersEx() > 0) {

						pasaporte_1.transferFocusBackward();

					} else {
						pasaporte_1.transferFocus();
					}

					e.consume();

				}
			}

		});
		frame.getContentPane().add(pasaporte_1);
		name = new JTextField();
		name.setBounds(227, 284, 99, 24);
		name.setEnabled(false);
		name.setColumns(1);
		name.addKeyListener(new KeyAdapter() {
			@Override
			public void keyPressed(KeyEvent e) {

				if (e.getKeyCode() == KeyEvent.VK_TAB) {

					if (e.getModifiersEx() > 0) {

						name.transferFocusBackward();

					} else {
						name.transferFocus();
					}

					e.consume();

				}
			}

		});
		frame.getContentPane().add(name);

		JLabel usesrname = new JLabel("旅客姓名");
		usesrname.setBounds(173, 285, 64, 22);
		frame.getContentPane().add(usesrname);

		btnpdf = new JButton("生成PDF");
		btnpdf.setBounds(237, 318, 231, 35);
		btnpdf.setIcon(new ImageIcon(Billete.class.getResource("/images/PDF.png")));
		btnpdf.setFont(new Font("SimSun", Font.BOLD, 11));
		btnpdf.addKeyListener(new KeyAdapter() {
			@Override
			public void keyPressed(KeyEvent e) {

				if (e.getKeyCode() == KeyEvent.VK_TAB) {

					if (e.getModifiersEx() > 0) {

						btnpdf.transferFocusBackward();

					} else {
						btnpdf.transferFocus();
					}

					e.consume();

				}
				if (e.getKeyCode() == KeyEvent.VK_ENTER) {

//					getPDF();
					getWord();

					e.consume();

				}

			}

		});
		btnpdf.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
//				getPDF();
				getWord();
			}
		});
		btnpdf.setEnabled(false);
		frame.getContentPane().add(btnpdf);

		chckbxNewCheckBox = new JCheckBox("PDF生成");
		chckbxNewCheckBox.setBounds(374, 259, 94, 23);
		chckbxNewCheckBox.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				if (chckbxNewCheckBox.isSelected()) {
					btnpdf.setEnabled(true);
					name.setEnabled(true);
//					pasaporte_1.setEnabled(true);
				}
				if (!chckbxNewCheckBox.isSelected()) {
					btnpdf.setEnabled(false);
					name.setEnabled(false);
					pasaporte_1.setEnabled(false);
				}
			}
		});
		frame.getContentPane().add(chckbxNewCheckBox);

		chckbxTop_1 = new JCheckBox("Top");
		chckbxTop_1.setSelected(true);
		chckbxTop_1.setBounds(351, 285, 56, 23);
		chckbxTop_1.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				if (chckbxTop_1.isSelected()) {
					frame.setAlwaysOnTop(true);
				}
				if (!chckbxTop_1.isSelected()) {
					frame.setAlwaysOnTop(false);
				}
			}
		});
		frame.getContentPane().add(chckbxTop_1);

	}

	public void getPDF() {
		/*
		 * 表单对应名字
		 * 
		 * 名字: nombre 护照: pasaporte
		 *
		 */
		Map<String, String> data = new HashMap<String, String>();

		/*
		 * String text = generatetext(); salida.setText(text);
		 * Billete.this.entrada.setText("");
		 */
		String username = Billete.this.name.getText();
		if (username == null || username.equals("")) {
			frame.setAlwaysOnTop(false);
			JOptionPane.showMessageDialog((Component) null, "请输入旅客名字！！", "嘿！季美女❤", 0);
			setTrue();
			return;
		}
		String pasaporte = Billete.this.pasaporte_1.getText();
		if (pasaporte == null || pasaporte.equals("")) {
			frame.setAlwaysOnTop(false);
			JOptionPane.showMessageDialog((Component) null, "请输入旅客护照！！", "嘿！季美女❤", 0);
			setTrue();
			return;
		}

		data.put("nombre", username);
		data.put("pasaporte", pasaporte);
		data.put("usuario", "试");
		PdfConvert pdf = new PdfConvert(data, username);
		name.setText("");
		pasaporte_1.setText("");
		entrada.setText("");
		try {
			pdf.getPDf();
			frame.setAlwaysOnTop(false);
			JOptionPane.showMessageDialog((Component) null, "文件" + username + ".pdf" + "已经生成！", "嘿！季美女❤", 1);
			setTrue();
		} catch (IOException | DocumentException e1) {
			frame.setAlwaysOnTop(false);
			JOptionPane.showMessageDialog((Component) null, "文件已经生成失败", "嘿！季美女❤", 1);
			setTrue();
		}
	}

	public void getAndcopy() {
		System.out.println();
		String code = Billete.this.entrada.getText();
		if (code == null || code.equals("")) {
			frame.setAlwaysOnTop(false);
			JOptionPane.showMessageDialog((Component) null, "请输入代码！！", "嘿！季美女❤", 0);
			setTrue();
			return;
		}
		this.pasajerosLs.clear();
		this.tiempoLs.clear();
		this.vuelosLs.clear();
		translate(code);
		String text = generatetext();
		salida.setText(text);
		Billete.this.copy(text);
		Billete.this.entrada.setText("");
		frame.setAlwaysOnTop(false);
		JOptionPane.showMessageDialog((Component) null, "结果已经成功复制到粘贴板！", "嘿！季美女❤", 1);
		setTrue();
	}

	public void copy(String text) {
		Toolkit.getDefaultToolkit().getSystemClipboard().setContents(new StringSelection(text), (ClipboardOwner) null);
	}

	public static String replaceNumber(String content) {
		String strMark = "\\d+";
		String strContent = "";
		strContent = content.replaceAll(strMark, "");
		return strContent;
	}

	public void translate(String code) {
		getFly();
		int cont = 1;
		boolean pasajero = true;
		boolean firstline = true;
		String code_reform = mergeLinesWithoutSequenceNumber(code); // 01.04.2024
		Scanner scanner = new Scanner(code_reform);
//		Scanner scanner = new Scanner(code);
		int ps_cont = 0;
		while (scanner.hasNext()) {
			String line = scanner.nextLine();

			Scanner scline = new Scanner(line);

			if (line.contains(".") && pasajero) {
				// Pasajero
				while (scline.hasNext()) {
					String res[] = scline.nextLine().split("[.]");

					for (int i = 1; i < res.length; i++) {
						String pasajeros2 = res[i];
						pasajeros2 = replaceNumber(pasajeros2);
						Pasajeros ps2 = new Pasajeros(pasajeros2);
						String id = "P" + cont;
						ps2.setId(id);
						pasajerosLs.add(ps2);
						cont++;
					}

					/*
					 * String pasajeros = res[1]; pasajeros= replaceNumber(pasajeros); Pasajeros ps
					 * = new Pasajeros(pasajeros); pasajerosLs.add(ps); cont++; if (res.length > 2)
					 * { String pasajeros2 = res[2]; pasajeros2= replaceNumber(pasajeros2);
					 * Pasajeros ps2 = new Pasajeros(pasajeros2); pasajerosLs.add(ps2); cont++;
					 * 
					 * }
					 */

				}
			}
//			01/04/2024 PDF INI
			else if (line.contains("SSR DOCS")) {

//				  9 SSR DOCS CA HK1 P/CHN/EL9792535/CHN/22SEP93/F/26FEB34/XIAO/Y
//			       IYI

				scline.next(); // id 9
				scline.next(); // SSR
				scline.next(); // DOCS
				scline.next(); // CA
				scline.next(); // HK1
				String data = scline.next(); // P/CHN/EL9792535/CHN/22SEP93/F/26FEB34/XIAO/YIYI
				if (scline.hasNext()) {
					data = data + scline.next();
				}
				if (scline.hasNext()) {
					data = data + scline.next();
				}
				String[] data_split = data.split("/");
				String nombre = data_split[7] + "/" + data_split[8];
//				if(data_split.length == 10) {
				if (this.pasajerosLs.size() > 1) {
//					 Si hay varios clientes 
					String id = data_split[data_split.length-1];

					for (int i = 0; i < this.pasajerosLs.size(); i++) {
						Pasajeros p = this.pasajerosLs.get(i);
						if (p.getId().contains(id)) {
							p.setPasaporte(data_split[2]);
							p.setGenero(data_split[5]);
							break;
						}
					}

				} else {
//					solo un cliente 
					this.pasajerosLs.get(0).setPasaporte(data_split[2]);
					this.pasajerosLs.get(0).setGenero(data_split[5]);
				}

			} else if (line.contains("FA PAX")) {
//				 14 FA PAX 999-6690500729/ETCA/EUR696.11/27MAR24/VLCI12260/78234
//			       063/S2-3
				scline.next(); // id 14
				scline.next(); // FA
				scline.next(); // PAX
				String billete = scline.next();
				if (scline.hasNext()) {
					billete = billete + scline.next();
				}
				if (scline.hasNext()) {
					billete = billete + scline.next();
				}
				String[] data_split = billete.split("/");
				if (this.pasajerosLs.size() > 1) {
					String id = data_split[data_split.length -1 ];
					for (int i = 0; i < this.pasajerosLs.size(); i++) {
						Pasajeros p = this.pasajerosLs.get(i);
						if (p.getId().contains(id)) {
							p.setNum_billete(data_split[0]);
							break;
						}
					}
				} else {

					this.pasajerosLs.get(0).setNum_billete(data_split[0]);
				}

				ps_cont++;

			}

//			01/04/2024 PDF FIN 
			else {

				// Vuelos
				pasajero = false;
				if (containMes(line)) {
					// Verificar si primer string es un numero
					String id = scline.next();
					String id_cont = Integer.toString(cont);
					if (!id.equals(id_cont) && firstline) {
						firstline = false;
						cont = Integer.valueOf(id);
						id_cont = Integer.toString(cont);
					}

					if (id.equals(id_cont)) {
						firstline = false;
						// si es una linea valida
						cont++;
						String fecha = "";
						String vuelo_id = scline.next();
						vuelo_id = vuelo_id + scline.next();
						while (scline.hasNext()) {
							fecha = scline.next();
							if (containMes(fecha)) {
								// si es una fecha salir de while
								break;
							}
						}
						String day = fecha.substring(0, 2);
						String mes = getMes(fecha.substring(2));
						scline.next();

						String ori_des = scline.next();
						String ori = ori_des.substring(0, 3);
						String des = ori_des.substring(3);
						if (this.map.containsKey(ori)) {
							ori = this.map.get(ori);
						}
						if (this.map.containsKey(des)) {
							des = this.map.get(des);
						}

						scline.next();
						String hora_ini = scline.next();
						while (scline.hasNext() && hora_ini.length() != 4) {
							hora_ini = scline.next();
						}

						String hora_fin = scline.next();
						if (hora_fin.length() < 4) {
							hora_ini = scline.next();
							hora_fin = scline.next();
						}
						// en caso de que hay hora de cerradura , lee siguiente
						// AF1729 T 12JUN 1 AGPCDG HK2 1640 1725 2005 *1A/E*

						String horafinal_verificar = scline.next(); // 2005
						if (horafinal_verificar.length() == 4 || horafinal_verificar.contains("+")) {
							hora_ini = hora_fin;
							hora_fin = horafinal_verificar;
						}

						StringBuffer stringBufferini = new StringBuffer(hora_ini);
						stringBufferini.insert(2, ":");

						StringBuffer stringBufferfin = new StringBuffer(hora_fin);
						stringBufferfin.insert(2, ":");
						VueloInformacion v = new VueloInformacion(vuelo_id, ori, des, stringBufferini.toString(),
								stringBufferfin.toString(), mes, day);
						this.vuelosLs.add(v);
					}

				}
			}

		}
	}

	public String generatetext() {
		String res = "";
		int cont = 1;
		boolean change = false;
		if (this.pasajerosLs.size() > 0) {
			for (Pasajeros p : this.pasajerosLs) {
				res = res + "乘客" + cont + ": " + p.getName() + "\n";
				cont++;
			}
		}
		if (this.vuelosLs.size() > 0) {
			for (int i = 0; i < this.vuelosLs.size(); i++) {
				change = false;
				VueloInformacion v1 = this.vuelosLs.get(i); // actual
				if (i == 0) {
					res = res + "【" + v1.getmes() + "月" + v1.getdia() + "日" + "】" + "\n";
					res = res + v1.getOrigen() + "-" + v1.getDestino() + "-->" + v1.getHora_start() + "-"
							+ v1.getHora_end() + "\n";
				} else {
					VueloInformacion v2 = this.vuelosLs.get(i - 1);
					int calendar = 0;
					if (v2.isDiaSiguinte()) {
						calendar = 1;
					}

					int time = getDifTime(Integer.parseInt(v2.getmes()), Integer.parseInt(v2.getdia()),
							Integer.parseInt(v2.getHoraFin()), Integer.parseInt(v2.getMinFin()),
							Integer.parseInt(v1.getmes()), Integer.parseInt(v1.getdia()),
							Integer.parseInt(v1.getHoraIni()), Integer.parseInt(v1.getMinIni()), calendar);
					int horas = time / 60;
					int minutos = time % 60;

					if (horas >= 24) {
						// SI mas de 24h
						for (EscalaTime e : this.tiempoLs) {
							res = res + e.getLugar() + "停留时间: " + e.getHora() + "小时" + e.getMinuto() + "分\n";
						}
						this.tiempoLs.clear();

						res = res + "---------<回程>---------\n";
						change = true;
					} else {
						EscalaTime t = new EscalaTime(horas, minutos, v1.getOrigen());
						this.tiempoLs.add(t);
					}
					if (change) {
						res = res + "【" + v1.getmes() + "月" + v1.getdia() + "日" + "】" + "\n";
					}
					res = res + v1.getOrigen() + "-" + v1.getDestino() + "-->" + v1.getHora_start() + "-"
							+ v1.getHora_end() + "\n";

				}
				if (i == this.vuelosLs.size() - 1) {
					for (EscalaTime e : this.tiempoLs) {
						res = res + e.getLugar() + "停留时间: " + e.getHora() + "小时" + e.getMinuto() + "分\n";
					}
				}

			}

		}

		res = res + "\n经济舱往返 欧\n" + "托运行李" + this.pack.getText() + " 件,每件" + this.peso.getText() + "公斤\n" + "手提行李"
				+ this.hand.getText() + "件" + this.hand_peso.getText() + " 公斤\n";
		return res;
	}

	public boolean containMes(String lines) {
		if (lines.contains("JAN") || lines.contains("FEB") || lines.contains("MAR") || lines.contains("APR")
				|| lines.contains("MAY") || lines.contains("JUN") || lines.contains("JUL") || lines.contains("AUG")
				|| lines.contains("SEP") || lines.contains("OCT") || lines.contains("NOV") || lines.contains("DEC")) {
			return true;

		} else {
			return false;
		}

	}

	public boolean isNum(String num) {
		for (int i = 0; i < num.length(); i++) {
			if (!Character.isDigit(num.charAt(i))) {
				return false;
			}
		}
		return true;
	}

	public int getDifDay(int mesi, int dayi, int mesf, int dayf) {
		int currentYear = Calendar.getInstance().get(1);
		Calendar calendar1 = Calendar.getInstance();
		calendar1.set(currentYear, mesi, dayi);
		Calendar calendar2 = Calendar.getInstance();
		calendar2.set(currentYear, mesf, dayf);
		if (mesi > mesf) {
			calendar2.add(1, 1);
		}
		return (int) ((calendar2.getTimeInMillis() - calendar1.getTimeInMillis()) / 86400000);
	}

	public int getDifTime(int mesi, int dayi, int horai, int mini, int mesf, int dayf, int horaf, int minf,
			int calendar) {
		int currentYear = Calendar.getInstance().get(1);
		Calendar calendar1 = Calendar.getInstance();
		calendar1.set(currentYear, mesi - 1, dayi, horai, mini, 0);
		if (calendar == 1) {
			calendar1.add(Calendar.DATE, 1);

		}
		Calendar calendar2 = Calendar.getInstance();
		calendar2.set(currentYear, mesf - 1, dayf, horaf, minf, 0);
		if (mesi > mesf) {
			calendar2.add(1, 1);
		}
		return (int) Math.abs((calendar1.getTimeInMillis() - calendar2.getTimeInMillis()) / 60000);
	}

	public void getFly() {
		try {
			BufferedReader reader = new BufferedReader(new FileReader(
					new File(String.valueOf(System.getProperty("user.dir")) + File.separator + "fly.txt")));
			while (true) {
				String line = reader.readLine();
				if (line == null) {
					reader.close();
					return;
				}
				System.out.println(line);
				String[] split = line.split(":");
				this.map.put(split[0], split[1]);
			}
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		} catch (IOException e2) {
			e2.printStackTrace();
		}
	}

	public void setTrue() {
		if (this.chckbxTop_1.isSelected()) {
			frame.setAlwaysOnTop(true);
		}
	}

	public String getMes(String mes) {
		switch (mes.hashCode()) {
		case 65027:
			if (mes.equals("APR")) {
				return "04";
			}
			break;
		case 65171:
			if (mes.equals("AUG")) {
				return "08";
			}
			break;
		case 67554:
			if (mes.equals("DEC")) {
				return "12";
			}
			break;
		case 69475:
			if (mes.equals("FEB")) {
				return "02";
			}
			break;
		case 73207:
			if (mes.equals("JAN")) {
				return "01";
			}
			break;
		case 73825:
			if (mes.equals("JUL")) {
				return "07";
			}
			break;
		case 73827:
			if (mes.equals("JUN")) {
				return "06";
			}
			break;
		case 76094:
			if (mes.equals("MAR")) {
				return "03";
			}
			break;
		case 76101:
			if (mes.equals("MAY")) {
				return "05";
			}
			break;
		case 77493:
			if (mes.equals("NOV")) {
				return "11";
			}
			break;
		case 78080:
			if (mes.equals("OCT")) {
				return "10";
			}
			break;
		case 81982:
			if (mes.equals("SEP")) {
				return "09";
			}
			break;
		}
		return "-1";
	}

	public static String reform(String line) {

		String res = "";
		String[] lines = line.toString().split("\n");

		for (int i = 0; i < lines.length; i++) {
			String currentLine = lines[i];
			String cLine = currentLine.trim();

			if (i < lines.length - 1) {
				if (startsWithDigit(lines[i + 1].trim())) {
					res = res + cLine + "\n";
				} else {
					res = res + cLine;
				}
			} else {
				res = res + cLine;
			}

		}

		return res;
	}

	public static boolean startsWithDigit(String line) {
		// 去除前导空格
		String trimmedLine = line.trim();

		// 判断处理后的字符串是否为空或其第一个字符是否为数字
		return !trimmedLine.isEmpty() && Character.isDigit(trimmedLine.charAt(0));
	}

	public static String mergeLinesWithoutSequenceNumber(String input) {
		StringBuilder output = new StringBuilder();
		String[] lines = input.split("\n");
		String previousLine = null;

		for (String line : lines) {
			// Trim to remove leading and trailing spaces
			line = line.trim();
			// Check if the line starts with a sequence number
			if (line.matches("^\\d+.*")) {
				// If it's a new numbered line and there's a previous line, append it
				if (previousLine != null) {
					output.append(previousLine).append("\n");
				}
				previousLine = line;
			} else {
				// If the line does not start with a number, merge it with the previous line
				if (previousLine != null) {
					previousLine += " " + line;
				} else {
					// If there's no previous line (which is unlikely given your context), just
					// treat this as the previous line
					previousLine = line;
				}
			}
		}
		// Don't forget to append the last line
		if (previousLine != null) {
			output.append(previousLine);
		}

//        System.out.println(output);
		return output.toString();
	}

	public void getWord() {
		String username = Billete.this.name.getText();
		if (username == null || username.equals("")) {
			frame.setAlwaysOnTop(false);
			JOptionPane.showMessageDialog((Component) null, "请输入旅客名字！！", "嘿！季美女❤", 0);
			setTrue();
			return;
		}
		
		String filelocal = String.valueOf(System.getProperty("user.dir"));
		String inputFilePath = filelocal + File.separator + "form1.docx"; // pdf模板
		String outputFilePath = filelocal + File.separator + "PDFConvert" + File.separator + username + ".docx"; // 替换为输出文件路径
		
		File file = new File(outputFilePath);
        
        // 检查文件是否存在
        if(file.exists()) {
        	// 删除文件
            boolean isDeleted = file.delete();
        	if(isDeleted) {
	        	frame.setAlwaysOnTop(false);
				JOptionPane.showMessageDialog((Component) null, "文件已经存在，已经删除旧文件 请重新点击生成！！", "嘿！季美女❤", 0);
        	}else {
        		frame.setAlwaysOnTop(false);
    			JOptionPane.showMessageDialog((Component) null, "删除失败 请手动删除", "嘿！季美女❤", 0);
        	}
        	setTrue();
			return;
        }
		
		String code = Billete.this.entrada.getText();
		translate(code);
		
		try (FileInputStream in = new FileInputStream(new File(inputFilePath));
				XWPFDocument document = new XWPFDocument(in)) {

			// 旅客信息
			XWPFTable tableL = document.getTables().get(0);

			for (int i = 0; i < this.pasajerosLs.size(); i++) {

				// 添加一个新行（在表格末尾）
				XWPFTableRow newRow = tableL.createRow();
				// 旅客姓名
				newRow.getCell(0).setText(this.pasajerosLs.get(i).getName());
				// 票号
				newRow.getCell(1).setText(this.pasajerosLs.get(i).getNum_billete());
				// 护照号
				newRow.getCell(2).setText(this.pasajerosLs.get(i).getPasaporte());
				// 居中
				newRow.getCell(0).getParagraphs().get(0).setAlignment(ParagraphAlignment.CENTER);
				newRow.getCell(1).getParagraphs().get(0).setAlignment(ParagraphAlignment.CENTER);
				newRow.getCell(2).getParagraphs().get(0).setAlignment(ParagraphAlignment.CENTER);

			}

			// 航班信息
			XWPFTable table = document.getTables().get(1);

			for (int i = 0; i < this.vuelosLs.size(); i++) {

				// 添加一个新行（在表格末尾）
				XWPFTableRow newRow = table.createRow();
				// vuelo id
				newRow.getCell(0).setText(this.vuelosLs.get(i).getId());
				// Origen
				newRow.getCell(1).setText(this.vuelosLs.get(i).getOrigen());
				// ini time
				newRow.getCell(2).setText(this.vuelosLs.get(i).getHora_start());
				// Destino
				newRow.getCell(3).setText(this.vuelosLs.get(i).getDestino());
				// arrive time
				newRow.getCell(4).setText(this.vuelosLs.get(i).getHora_end());

				// 居中
				newRow.getCell(0).getParagraphs().get(0).setAlignment(ParagraphAlignment.CENTER);
				newRow.getCell(1).getParagraphs().get(0).setAlignment(ParagraphAlignment.CENTER);
				newRow.getCell(2).getParagraphs().get(0).setAlignment(ParagraphAlignment.CENTER);
				newRow.getCell(3).getParagraphs().get(0).setAlignment(ParagraphAlignment.CENTER);
				newRow.getCell(4).getParagraphs().get(0).setAlignment(ParagraphAlignment.CENTER);

			}
			
			// 创建映射来存储占位符和替换文本
            Map<String, String> placeholders = new HashMap<>();
            placeholders.put("${placeholder}", "Replacement Text 1");
            placeholders.put("${placeholder2}", "Replacement Text 2");
			   // 获取文档中的段落 填写编号
            for (XWPFParagraph paragraph : document.getParagraphs()) {
            	 // 替换文本
                for (XWPFRun run : paragraph.getRuns()) {
                    String runText = run.getText(run.getTextPosition());
                    for (Map.Entry<String, String> entry : placeholders.entrySet()) {
                        String placeholder = entry.getKey();
                        String replacementText = entry.getValue();
                        if (runText != null && runText.contains(placeholder)) {
                            runText = runText.replace(placeholder, replacementText);
                            run.setText(runText, 0);
                        }
                    }
                }
            }
			

			// 将修改保存到一个新文件
			try (FileOutputStream out = new FileOutputStream(new File(outputFilePath))) {
				document.write(out);
				document.close();
				frame.setAlwaysOnTop(false);
				JOptionPane.showMessageDialog((Component) null, "文件" + username + ".pdf" + "已经生成！", "嘿！季美女❤", 1);
				setTrue();
			} catch (IOException e) {
				frame.setAlwaysOnTop(false);
				JOptionPane.showMessageDialog((Component) null, "文件已经生成失败", "嘿！季美女❤", 1);
				setTrue();
			}

		} catch (IOException e) {
			e.printStackTrace();
		}
	}
	
	public void WordToPDF(String wordFile , String pdfFile ) {
		
	}

}
