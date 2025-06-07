import { Module } from '@nestjs/common';
import { ConfigModule as NestConfigModule } from '@nestjs/config';

@Module({
  imports: [
    NestConfigModule.forRoot({
      isGlobal: true, // Make the configuration available globally
      envFilePath: '.env', // Specify the path to the .env file
    }),
  ],
  exports: [NestConfigModule], // Export NestConfigModule to be used in other modules
})
export class ConfigModule {}
