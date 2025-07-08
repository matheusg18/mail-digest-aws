output "telegram_webhook_url" {
  description = "The public URL for the Telegram webhook function."
  value       = google_cloudfunctions2_function.telegram_webhook_function.service_config[0].uri
}
