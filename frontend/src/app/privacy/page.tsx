import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';

export default function PrivacyPage() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <section className="pt-24 pb-20 max-w-3xl mx-auto px-4">
        <h1 className="section-title">プライバシーポリシー</h1>
        <div className="prose prose-sm text-gray-600 space-y-4">
          <p>Kenko AI Healthcare Platform（以下「当社」）は、ユーザーの個人情報保護を最重要事項と考え、以下のプライバシーポリシーを定めます。</p>
          <h2 className="text-lg font-semibold text-primary-800">1. 収集する情報</h2>
          <p>氏名、メールアドレス、電話番号、生年月日、健康チェックインデータ、LINE User ID、位置情報（病院検索時）等を収集する場合があります。</p>
          <h2 className="text-lg font-semibold text-primary-800">2. 利用目的</h2>
          <p>AI医療受付サービスの提供、予約管理、健康フォローアップ、病院推薦、サブスクリプション管理のために利用します。</p>
          <h2 className="text-lg font-semibold text-primary-800">3. 第三者提供</h2>
          <p>法令に基づく場合を除き、ユーザーの同意なく個人情報を第三者に提供しません。</p>
          <h2 className="text-lg font-semibold text-primary-800">4. お問い合わせ</h2>
          <p>privacy@kenko-ai.jp</p>
        </div>
      </section>
      <Footer />
    </div>
  );
}
