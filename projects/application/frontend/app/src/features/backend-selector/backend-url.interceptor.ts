import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { BackendConfigService } from './backend-config.service';

export const backendUrlInterceptor: HttpInterceptorFn = (req, next) => {
  const backendConfig = inject(BackendConfigService);
  const baseUrl = backendConfig.getBaseUrl();
  if (baseUrl && !req.url.startsWith('http')) {
    return next(req.clone({ url: `${baseUrl}${req.url}` }));
  }
  return next(req);
};
