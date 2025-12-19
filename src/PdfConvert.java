import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

import com.itextpdf.text.DocumentException;
import com.itextpdf.text.pdf.AcroFields;
import com.itextpdf.text.pdf.BaseFont;
import com.itextpdf.text.pdf.PdfContentByte;
import com.itextpdf.text.pdf.PdfReader;
import com.itextpdf.text.pdf.PdfStamper;

public class PdfConvert {

	private Map<String, String> data;
	private String username;

	public PdfConvert(Map<String, String> data, String filename) {
		super();
		this.data = data;
		this.username = filename;
	}

	public void getPDf() throws IOException, DocumentException {
		String filelocal = String.valueOf(System.getProperty("user.dir"));
		String fileName = filelocal + File.separator + "form1.pdf"; // pdf模板
		String output = filelocal + File.separator+"PDFConvert"+File.separator + username+".pdf";
		PdfReader reader = new PdfReader(fileName);
		ByteArrayOutputStream bos = new ByteArrayOutputStream();
		// 将要生成的目标PDF文件名称
		PdfStamper ps = new PdfStamper(reader, bos);
		PdfContentByte under = ps.getUnderContent(1);

		/* 使用中文字体 */
		BaseFont bf = BaseFont.createFont("STSong-Light", "UniGB-UCS2-H", BaseFont.NOT_EMBEDDED);
		ArrayList<BaseFont> fontList = new ArrayList<BaseFont>();
		fontList.add(bf);

		/* 取出报表模板中的所有字段 */
		AcroFields fields = ps.getAcroFields();
		fields.setSubstitutionFonts(fontList);
		fillData(fields, this.data);

		/* 必须要调用这个，否则文档不会生成的 */
		ps.setFormFlattening(true);
		ps.close();

		OutputStream fos = new FileOutputStream(new File(output));
		fos.write(bos.toByteArray());
		fos.flush();
		fos.close();
		bos.close();
	}

	public static void fillData(AcroFields fields, Map<String, String> data) throws IOException, DocumentException {
		for (String key : data.keySet()) {
			String value = data.get(key);
			fields.setField(key, value); // 为字段赋值,注意字段名称是区分大小写的
		}
	}

	public static Map<String, String> data() {
		Map<String, String> data = new HashMap<String, String>();
		data.put("name", "test：");
		data.put("part", "xx第10000001号");
		// data.put("amount", "1000");
		// data.put("date","2015年7月7日");
		return data;

	}
}
