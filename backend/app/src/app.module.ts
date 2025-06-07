import { Module } from '@nestjs/common';
import { ConfigModule } from './config'; // Import the new ConfigModule
import { AppController } from './app.controller';
import { AppService } from './app.service';

@Module({
  imports: [
    ConfigModule, // Add ConfigModule here
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
