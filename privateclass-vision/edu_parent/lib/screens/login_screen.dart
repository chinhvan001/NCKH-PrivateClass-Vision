import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';
import 'home_screen.dart';

class LoginScreen extends StatelessWidget {
  const LoginScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 28),
          child: Column(
            children: [
              const Spacer(flex: 2),
              // Logo
              Image.asset(
                'assets/images/logo.png',
                width: 180,
                height: 180,
              ),
              const Spacer(flex: 1),
              // Illustration
              Container(
                height: 160,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(16),
                  color: AppColors.accentLight,
                ),
                child: const Center(
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.family_restroom, size: 80, color: AppColors.primary),
                    ],
                  ),
                ),
              ),
              const Spacer(flex: 1),
              const Text(
                'Chào mừng bạn!',
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Đăng nhập để tiếp tục',
                style: AppTextStyles.body2,
              ),
              const SizedBox(height: 32),
              // Google Sign In Button
              SizedBox(
                width: double.infinity,
                height: 52,
                child: OutlinedButton.icon(
                  onPressed: () {
                    Navigator.pushReplacement(
                      context,
                      MaterialPageRoute(builder: (_) => const HomeScreen()),
                    );
                  },
                  icon: Container(
                    width: 24,
                    height: 24,
                    decoration: const BoxDecoration(
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.g_mobiledata,
                      color: AppColors.red,
                      size: 28,
                    ),
                  ),
                  label: const Text(
                    'Đăng nhập bằng Google',
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                      color: AppColors.textPrimary,
                    ),
                  ),
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: AppColors.divider, width: 1.5),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    backgroundColor: Colors.white,
                  ),
                ),
              ),
              const Spacer(flex: 2),
              Text(
                'Chúng tôi không chia sẻ thông tin\ncủa bạn với bất kỳ bên thứ ba.',
                textAlign: TextAlign.center,
                style: AppTextStyles.small.copyWith(color: AppColors.textHint),
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }
}
