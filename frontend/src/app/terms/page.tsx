import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';

export default function TermsPage() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <section className="pt-24 pb-20 max-w-3xl mx-auto px-4">
        <h1 className="section-title">利用規約</h1>
        <div className="prose prose-sm text-gray-600 space-y-4">
          <p>本規約は、Kenko AI Healthcare Platform（以下「本サービス」）の利用条件を定めるものです。</p>
          <h2 className="text-lg font-semibold text-primary-800">1. サービス内容</h2>
          <p>本サービスはAI支援型の医療情報提供・予約支援・病院検索プラットフォームです。医療診断を提供するものではありません。</p>
          <h2 className="text-lg font-semibold text-primary-800">2. 免責事項</h2>
          <p>AIによる症状評価は参考情報であり、医師の診断に代わるものではありません。緊急時は119番または最寄りの救急医療機関をご利用ください。</p>
          <h2 className="text-lg font-semibold text-primary-800">3. サブスクリプション</h2>
          <p>7日間の無料トライアル後、有料プランへの登録が必要です。解約はダッシュボードから可能です。</p>
          <h2 className="text-lg font-semibold text-primary-800">4. 禁止事項</h2>
          <p>虚偽情報の登録、システムへの不正アクセス、他ユーザーへの迷惑行為を禁止します。</p>
        </div>
      </section>
      <Footer />
    </div>
  );
}
