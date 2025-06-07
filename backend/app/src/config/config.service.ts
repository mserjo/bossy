import { Injectable } from '@nestjs/common';
import { ConfigService as NestConfigService } from '@nestjs/config';

@Injectable()
export class ConfigService {
  constructor(private nestConfigService: NestConfigService) {}

  get(key: string): string | undefined {
    return this.nestConfigService.get<string>(key);
  }
}
