import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.KeyEvent;
import java.awt.event.KeyListener;

public class Main extends JFrame {
    // 假设的用户名和密码
    private static final String USERNAME = "ADMIN";
    private static final String PASSWORD = "shixiaomin";
    private JTextField usernameField; // 将文本框定义为类的成员变量
    private JPasswordField passwordField; // 将文本框定义为类的成员变量
    public Main() {
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
        setTitle("季露露专属 登入界面");
        setSize(369, 155);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setResizable(false);
        setIconImage(Toolkit.getDefaultToolkit().getImage("path/to/your/image.png")); // 更改为你的图片路径
        setBounds(600, 300, 400, 200);
        // 使用BorderLayout
        getContentPane().setLayout(new BorderLayout());

        // 用户名和密码面板
        JPanel credentialsPanel = new JPanel();
        credentialsPanel.setLayout(new GridLayout(2, 2));
        JLabel usernameLabel = new JLabel("用户名:");
        usernameLabel.setHorizontalAlignment(SwingConstants.CENTER);
        usernameField = new JTextField(10);
        usernameField.setHorizontalAlignment(SwingConstants.CENTER);
        usernameField.setText(USERNAME);
        JLabel passwordLabel = new JLabel("密码:");
        passwordLabel.setHorizontalAlignment(SwingConstants.CENTER);
        passwordField = new JPasswordField(10);
        passwordField.setHorizontalAlignment(SwingConstants.CENTER);
        credentialsPanel.add(usernameLabel);
        credentialsPanel.add(usernameField);
        credentialsPanel.add(passwordLabel);
        credentialsPanel.add(passwordField);

        // 登录按钮面板
        JPanel buttonPanel = new JPanel();
        JButton loginButton = new JButton("登录");
        buttonPanel.add(loginButton);

        loginButton.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                login();
            }
        });

        // 添加键盘监听器，用于在按下Enter键时执行登录操作
        KeyListener keyListener = new KeyListener() {
            @Override
            public void keyTyped(KeyEvent e) {}

            @Override
            public void keyPressed(KeyEvent e) {}

            @Override
            public void keyReleased(KeyEvent e) {
                if (e.getKeyCode() == KeyEvent.VK_ENTER) {
                    login();
                }
            }
        };

        usernameField.addKeyListener(keyListener);
        passwordField.addKeyListener(keyListener);

        // 将面板添加到JFrame
        getContentPane().add(credentialsPanel, BorderLayout.CENTER);
        getContentPane().add(buttonPanel, BorderLayout.SOUTH);

        setVisible(true);
    }

    // 登录方法
    private void login() {
        String enteredUsername = usernameField.getText();
        String enteredPassword = new String(passwordField.getPassword());
        if (authenticate(enteredUsername, enteredPassword)) {
            JOptionPane.showMessageDialog(Main.this, "登录成功！");
            dispose();
            new Billete().frame.setVisible(true); // 假设这是你想要打开的下一个窗口
            // 这里可以添加跳转到下一个界面的逻辑
        } else {
            JOptionPane.showMessageDialog(Main.this, "用户名或密码错误！", "错误", JOptionPane.ERROR_MESSAGE);
        }
    }

    // 验证用户名和密码是否正确的方法
    private static boolean authenticate(String username, String password) {
        return USERNAME.equals(username) && PASSWORD.equals(password);
    }
    public static void main(String[] args) {
        SwingUtilities.invokeLater(new Runnable() {
            @Override
            public void run() {
                new Main();
            }
        });
    }
}
