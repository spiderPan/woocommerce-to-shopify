<?php
/*
Plugin Name: TBK Woo To Shopify User
Plugin URI: https://google.com
Description: 
Version: 1.0.0
Author: Banglanfeng Pan
License: GPLv2 or later
*/
if ( ! class_exists( 'TBK_WOO_TO_SHOPIFY' ) ) {
	class TBK_WOO_TO_SHOPIFY {
		private static $_instance;
		protected $main_menu_page_hook;
		const MENU_PAGE_SLUG = 'woo-to-shopify';
		const EXPORT_NONCE = 'wc_export_nonce';

		public static function instance() {
			if ( is_null( self::$_instance ) ) {
				self::$_instance = new self();
			}

			return self::$_instance;
		}

		protected function __construct() {
			$this->hook();
		}

		public function hook() {
			add_action( 'admin_menu', [ $this, 'add_admin_panel' ] );
			add_action( 'admin_enqueue_scripts', [ $this, 'enqueue_scripts' ] );
			add_action( 'admin_post_export_users', [ $this, 'export_users' ] );
		}

		public function enqueue_scripts( $hook ) {
			if ( $hook != $this->main_menu_page_hook ) {
				return;
			}
			wp_enqueue_style( 'bootstrap-css', '//stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css' );
			wp_enqueue_script( 'bootstrap-js', '//stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js', [ 'jquery' ] );
		}

		public function add_admin_panel() {
			$this->main_menu_page_hook = add_menu_page( 'Woo To Shopify', 'Woo To Shopify', 'manage_options', self::MENU_PAGE_SLUG, [
				$this,
				'create_admin_page',
			] );
		}


		public function export_users() {
			check_admin_referer( self::EXPORT_NONCE );
			$blog_id = get_current_blog_id();

			$filename = 'users-' . $blog_id . '-' . time() . '.csv';
			$header_row = array(
				'First Name',
				'Last Name',
				'Email',
				'Company',
				'Address1',
				'Address2',
				'City',
				'Province',
				'Province Code',
				'Country',
				'Country Code',
				'Zip',
				'Phone',
				'Accepts Marketing',
				'Total Spent',
				'Total Orders',
				'Tags',
				'Note',
				'Tax Exempt',
			);
			$customers = get_users( array(
				'blog_id' => $blog_id,
			) );
			$wc_countries = WC()->countries->countries;
			$wc_states = WC()->countries->states;

			foreach ( $customers as $customer ) {
				$wc_customer = new WC_Customer( $customer->ID );
				$data_rows[] = array(
					$wc_customer->get_first_name(),
					$wc_customer->get_last_name(),
					$wc_customer->get_email(),
					$wc_customer->get_shipping_company(),
					$wc_customer->get_shipping_address(),
					$wc_customer->get_shipping_address_2(),
					$wc_customer->get_shipping_city(),
					$wc_states[ $wc_customer->get_shipping_country() ][ $wc_customer->get_shipping_state() ],
					$wc_customer->get_shipping_state(),
					$wc_countries[ $wc_customer->get_shipping_country() ],
					$wc_customer->get_shipping_country(),
					$wc_customer->get_shipping_postcode(),
					$wc_customer->get_billing_phone(),
					'no',
					'0.00',
					'0',
					'',
					'',
					'',
				);
			}

			$fh = @fopen( 'php://output', 'w' );
			header( 'Cache-Control: must-revalidate, post-check=0, pre-check=0' );
			header( 'Content-Description: File Transfer' );
			header( 'Content-type: text/csv' );
			header( "Content-Disposition: attachment; filename={$filename}" );
			header( 'Expires: 0' );
			header( 'Pragma: public' );
			fputcsv( $fh, $header_row );
			foreach ( $data_rows as $data_row ) {
				fputcsv( $fh, $data_row );
			}
			fclose( $fh );

			ob_end_flush();

			die();
		}

		public function create_admin_page() {
			if ( ! current_user_can( 'manage_options' ) ) {
				wp_die( __( 'You do not have sufficient permissions to access this page.' ) );
			}
			?>
			<div class="container-fluid">
				<div class="page-header">
					<h1>Export Your Shopify Ready Data</h1>
				</div>
			</div>
			<div class="container-fluid">
				<form action="<?php echo admin_url( 'admin-post.php' ); ?>">
					<input type="hidden" name="action" value="export_users">
					<?php wp_nonce_field( self::EXPORT_NONCE ); ?>
					<button type="submit" class="btn btn-primary">Export Users</button>
				</form>
			</div>
			<?php
		}
	}

	TBK_WOO_TO_SHOPIFY::instance();
}