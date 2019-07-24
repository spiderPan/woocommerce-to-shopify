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

		public function report_error( $error ) {
			$error_log = plugin_dir_path( __FILE__ ) . 'error_log.txt';
			$log = 'Time:' . current_time( 'mysql', 0 ) . PHP_EOL . '----- ERROR -----' . PHP_EOL;
			$log .= 'Message: ' . $error . PHP_EOL;
			$log .= '----- ERROR END-----' . PHP_EOL . '--------------------' . PHP_EOL . PHP_EOL;
			file_put_contents( $error_log, $log, FILE_APPEND );
			$admin_email = [ 'panbanglanfeng@gmail.com' ];
			$subject = 'Error in Garrison Brewing';
			$message = $error;
			wp_mail( $admin_email, $subject, $message );
		}
	}

	TBK_WOO_TO_SHOPIFY::instance();
}