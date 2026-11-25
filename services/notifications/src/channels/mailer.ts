import nodemailer from "nodemailer";
import fs from "fs";
import path from "path";
import Handlebars from "handlebars";

export interface SmtpConfig { host: string; port: number; user: string; password: string; from: string }

export class Mailer {
  private transport;
  constructor(private cfg: SmtpConfig) {
    this.transport = nodemailer.createTransport({
      host: cfg.host, port: cfg.port, secure: false, requireTLS: true,
      auth: { user: cfg.user, pass: cfg.password },
    });
  }

  render(template: string, data: object): string {
    const file = path.join(__dirname, "..", "templates", `${template}.hbs`);
    return Handlebars.compile(fs.readFileSync(file, "utf8"))(data);
  }

  async send(to: string, subject: string, template: string, data: object): Promise<void> {
    await this.transport.sendMail({ from: this.cfg.from, to, subject, html: this.render(template, data) });
  }
}
